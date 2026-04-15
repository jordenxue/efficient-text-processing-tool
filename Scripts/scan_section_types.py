"""
scan_section_types.py
扫描 chunks，识别可能的非 story_scene chunk，输出待审清单。
纯规则，不调 LLM。
"""

import os
import re
import json
import glob

# === 配置 ===
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS_DIR = os.path.join(PROJECT_ROOT, "chunks")
# canon 输出目录——实际路径为 outputs/canon
CANON_DIR = os.path.join(PROJECT_ROOT, "outputs", "canon")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "review")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scan_candidates.jsonl")

# === 规则定义 ===

# author_meta 信号词（编辑提示、作者按语）
AUTHOR_META_PATTERNS = [
    r"作者[按注]",
    r"编者[按注]",
    r"本[章卷](?:完|结束)",
    r"(?:感谢|致谢)(?:读者|支持)",
    r"求[票月推]",
    r"上架感言",
    r"请假条",
    r"更新(?:说明|通知)",
    r"番外预告",
]

# front_matter 信号词（目录、版权、前言）
FRONT_MATTER_PATTERNS = [
    r"^(?:目录|contents)$",
    r"(?:版权|copyright)",
    r"(?:前言|序言|楔子|引言)",
    r"(?:人物介绍|人物表|出场人物)",
    r"^第[零〇一二三四五六七八九十百千万]+[卷部篇]",
]

# in_universe_document 信号词（故事内文书）
IN_UNIVERSE_DOC_PATTERNS = [
    r"实验记录",
    r"(?:档案|报告)(?:编号|编码)",
    r"(?:日志|日记)(?:条目|记录)",
    r"(?:密级|机密等级)",
    r"(?:收件人|发件人|致：|To：)",
    r"(?:附录|appendix)",
]

# setting_exposition 信号词（世界观设定说明）
SETTING_EXPOSITION_PATTERNS = [
    r"(?:职业|阶级|等级)(?:体系|系统|说明|介绍|一览)",
    r"(?:魔法|技能|能力)(?:体系|系统|分类|说明)",
    r"(?:世界观|背景)(?:设定|说明|介绍)",
    r"(?:种族|势力|阵营)(?:介绍|说明|一览)",
]


def compile_patterns(pattern_list):
    return [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in pattern_list]


RULES = [
    ("author_meta", compile_patterns(AUTHOR_META_PATTERNS)),
    ("front_matter", compile_patterns(FRONT_MATTER_PATTERNS)),
    ("in_universe_document", compile_patterns(IN_UNIVERSE_DOC_PATTERNS)),
    ("setting_exposition", compile_patterns(SETTING_EXPOSITION_PATTERNS)),
]


def has_dialogue(text):
    """检查文本中是否包含对话标记"""
    dialogue_markers = [
        r'[""「」『』【】]',  # 各种引号
        r'(?:说|道|问|答|喊|叫|笑|叹|吼)(?:道|着|了)?[：:，,]',  # 对话动词
    ]
    for pattern in dialogue_markers:
        if re.search(pattern, text):
            return True
    return False


def has_narrative_verbs(text):
    """检查文本中是否包含叙事动词（粗略判断）"""
    narrative_patterns = [
        r"(?:走|跑|跳|飞|坐|站|躺|蹲|爬)",
        r"(?:看着|望着|盯着|注视|凝视)",
        r"(?:拿起|放下|举起|扔出|抓住)",
        r"(?:心想|暗想|心中|内心|脑海)",
    ]
    count = 0
    for pattern in narrative_patterns:
        count += len(re.findall(pattern, text))
    return count >= 3  # 至少 3 个叙事动词才算有叙事性


def load_canon_output(chunk_id):
    """尝试加载对应的 canon 输出"""
    # 尝试多种可能的路径
    for canon_dir in [CANON_DIR, os.path.join(PROJECT_ROOT, "canon")]:
        canon_file = os.path.join(canon_dir, f"{chunk_id}.json")
        if os.path.exists(canon_file):
            try:
                with open(canon_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
    return None


def analyze_chunk(chunk_id, text, meta):
    """分析单个 chunk，返回 (suggested_type, confidence, reasons) 或 None"""
    reasons = []
    suggested_type = None
    confidence = "uncertain"

    # 第一遍：关键词匹配
    for type_name, patterns in RULES:
        matched = []
        for p in patterns:
            m = p.search(text[:500])  # 只看前 500 字（标题/开头区域）
            if m:
                matched.append(m.group())
        if matched:
            suggested_type = type_name
            reasons.append(f"关键词命中: {', '.join(matched[:3])}")
            break  # 按优先级，命中第一个即停

    if suggested_type is None:
        # 第二遍：结构特征检测
        lines = text.strip().split("\n")
        non_empty_lines = [l.strip() for l in lines if l.strip()]

        # 检测：大量编号列表（可能是设定说明）
        numbered_lines = sum(1 for l in non_empty_lines if re.match(r"^\d+[\.\、\)]", l))
        if len(non_empty_lines) > 5 and numbered_lines / len(non_empty_lines) > 0.4:
            suggested_type = "setting_exposition"
            reasons.append(f"编号列表占比 {numbered_lines}/{len(non_empty_lines)}")

        # 检测：无对话 + 无叙事动词（可能是说明文）
        if suggested_type is None and len(text) > 300:
            if not has_dialogue(text) and not has_narrative_verbs(text):
                suggested_type = "setting_exposition"
                reasons.append("无对话标记且叙事动词不足")
                confidence = "uncertain"  # 这条规则不够强，降为 uncertain

    if suggested_type is None:
        return None  # 没有可疑信号，视为正常 story_scene

    # 用 canon 输出辅助判断
    canon = load_canon_output(chunk_id)
    if canon:
        events = canon.get("events", [])
        characters = canon.get("characters", [])
        if len(events) == 0 and len(characters) == 0:
            reasons.append("canon 输出无事件且无角色")
            confidence = "high"
        elif len(events) == 0:
            reasons.append("canon 输出无事件")

    # 关键词命中 + 有 canon 佐证 → high
    if len(reasons) >= 2 and any("关键词" in r for r in reasons):
        confidence = "high"
    # 单纯关键词命中但无 canon 佐证 → uncertain（保守）
    elif len(reasons) == 1 and "关键词" in reasons[0]:
        confidence = "uncertain"

    return {
        "chunk_id": chunk_id,
        "suggested_type": suggested_type,
        "confidence": confidence,
        "reasons": reasons,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 收集所有 chunk
    txt_files = sorted(glob.glob(os.path.join(CHUNKS_DIR, "*.txt")))
    print(f"找到 {len(txt_files)} 个 chunk 文件")

    candidates = []
    errors = []

    for txt_path in txt_files:
        chunk_id = os.path.splitext(os.path.basename(txt_path))[0]
        meta_path = os.path.join(CHUNKS_DIR, f"{chunk_id}.meta.json")

        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            errors.append({"chunk_id": chunk_id, "error": f"读取 txt 失败: {e}"})
            continue

        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        result = analyze_chunk(chunk_id, text, meta)
        if result:
            candidates.append(result)

    # 写出结果
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for c in candidates:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # 统计输出
    high_count = sum(1 for c in candidates if c["confidence"] == "high")
    uncertain_count = sum(1 for c in candidates if c["confidence"] == "uncertain")

    print(f"\n扫描完成:")
    print(f"  总 chunk 数: {len(txt_files)}")
    print(f"  候选非 story_scene: {len(candidates)}")
    print(f"    high confidence: {high_count}")
    print(f"    uncertain: {uncertain_count}")
    print(f"  输出文件: {OUTPUT_FILE}")

    if errors:
        print(f"  读取错误: {len(errors)}")
        error_file = os.path.join(OUTPUT_DIR, "scan_errors.jsonl")
        with open(error_file, "w", encoding="utf-8") as f:
            for e in errors:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"  错误日志: {error_file}")

    # 按类型分组汇总
    type_counts = {}
    for c in candidates:
        t = c["suggested_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"\n按类型分布:")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")


if __name__ == "__main__":
    main()
