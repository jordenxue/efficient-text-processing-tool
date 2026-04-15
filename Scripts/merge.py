"""
merge.py — 汇总 outputs/canon/ 和 outputs/style/ 的数据，生成知识库文件
用法：python scripts/merge.py
"""

import os
import sys
import json
import datetime
from collections import defaultdict

# ── 路径基准 ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CANON_DIR = os.path.join(BASE_DIR, "outputs", "canon")
STYLE_DIR = os.path.join(BASE_DIR, "outputs", "style")
KB_DIR    = os.path.join(BASE_DIR, "kb")

MASTER_KB_PATH       = os.path.join(KB_DIR, "master_kb.json")
PROMPT_CONTEXT_PATH  = os.path.join(KB_DIR, "prompt_context.md")
CHARACTER_IDX_PATH   = os.path.join(KB_DIR, "character_index.json")
LOCATION_IDX_PATH    = os.path.join(KB_DIR, "location_index.json")
EVENT_IDX_PATH       = os.path.join(KB_DIR, "event_index.json")
RELATIONSHIP_IDX_PATH = os.path.join(KB_DIR, "relationship_index.json")
STYLE_SUMMARY_PATH   = os.path.join(KB_DIR, "style_summary.json")

os.makedirs(KB_DIR, exist_ok=True)


# ── 数据加载 ──────────────────────────────────────────────────────────────────

def load_dir(directory: str) -> dict[str, dict]:
    """
    读取目录下所有 .json 文件，返回 {chunk_id: record}。
    忽略无法解析的文件并打印警告。
    """
    result = {}
    if not os.path.isdir(directory):
        return result
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(directory, fname)
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            cid = data.get("chunk_id", fname[:-5])
            result[cid] = data
        except (json.JSONDecodeError, OSError) as e:
            print(f"警告：跳过无法读取的文件 {fname}：{e}", file=sys.stderr)
    return result


# ── 合并逻辑 ──────────────────────────────────────────────────────────────────

META_FIELDS = ("source_file", "chapter_hint", "char_start", "char_end")
CANON_PAYLOAD_FIELDS = ("summary", "characters", "events", "locations",
                        "time_markers", "relationships")
STYLE_PAYLOAD_FIELDS = ("narration_tone", "dialogue_density", "prose_features",
                        "key_dialogues", "style_tags")


def merge_records(canon_map: dict[str, dict],
                  style_map: dict[str, dict]) -> list[dict]:
    """
    按 chunk_id 合并 canon 和 style 数据。
    chunk 至少在其中一个 map 中存在才会被输出。
    排序：按 chunk_id 字典序。
    """
    all_ids = sorted(set(canon_map) | set(style_map))
    merged = []
    for cid in all_ids:
        canon_rec = canon_map.get(cid, {})
        style_rec = style_map.get(cid, {})

        # 元数据优先从 canon 取，其次 style
        base_rec = canon_rec if canon_rec else style_rec
        meta = {k: base_rec.get(k, "") for k in META_FIELDS}

        entry = {"chunk_id": cid, **meta}

        # canon 载荷
        if canon_rec:
            entry["canon"] = {k: canon_rec.get(k) for k in CANON_PAYLOAD_FIELDS
                              if k in canon_rec}
        else:
            entry["canon"] = None

        # style 载荷
        if style_rec:
            entry["style"] = {k: style_rec.get(k) for k in STYLE_PAYLOAD_FIELDS
                              if k in style_rec}
        else:
            entry["style"] = None

        merged.append(entry)
    return merged


# ── 索引构建 ──────────────────────────────────────────────────────────────────

def build_character_index(canon_map: dict[str, dict]) -> dict:
    """
    从 canon 数据构建人物索引，包含行为和情绪汇总。
    返回 {name: {count, chunks, actions, emotions}}
    """
    index: dict = {}
    for cid, rec in canon_map.items():
        characters = rec.get("characters", [])
        if not isinstance(characters, list):
            continue
        for char in characters:
            if not isinstance(char, dict):
                continue
            name = char.get("name", "").strip()
            if not name:
                continue
            if name not in index:
                index[name] = {"count": 0, "chunks": [], "actions": [], "emotions": []}
            index[name]["count"] += 1
            if cid not in index[name]["chunks"]:
                index[name]["chunks"].append(cid)
            action = char.get("action", "").strip()
            if action and action not in index[name]["actions"]:
                index[name]["actions"].append(action)
            emotion = char.get("emotion", "").strip()
            if emotion and emotion not in index[name]["emotions"]:
                index[name]["emotions"].append(emotion)

    return dict(sorted(index.items(), key=lambda x: x[1]["count"], reverse=True))


def build_location_index(canon_map: dict[str, dict]) -> dict:
    """从 canon locations 字段构建地点索引。"""
    index: dict = {}
    for cid, rec in canon_map.items():
        for loc in rec.get("locations", []):
            if not isinstance(loc, str) or not loc.strip():
                continue
            loc = loc.strip()
            if loc not in index:
                index[loc] = {"count": 0, "chunks": []}
            index[loc]["count"] += 1
            if cid not in index[loc]["chunks"]:
                index[loc]["chunks"].append(cid)
    return dict(sorted(index.items(), key=lambda x: x[1]["count"], reverse=True))


def build_event_index(canon_map: dict[str, dict]) -> dict:
    """
    从 canon events 字段构建事件索引（以事件描述为键）。
    返回 {event_text: {count, chunks, causes, results}}
    """
    index: dict = {}
    for cid, rec in canon_map.items():
        for ev in rec.get("events", []):
            if not isinstance(ev, dict):
                continue
            event_text = ev.get("event", "").strip()
            if not event_text:
                continue
            if event_text not in index:
                index[event_text] = {"count": 0, "chunks": [], "causes": [], "results": []}
            index[event_text]["count"] += 1
            if cid not in index[event_text]["chunks"]:
                index[event_text]["chunks"].append(cid)
            cause = ev.get("cause", "").strip()
            if cause and cause not in index[event_text]["causes"]:
                index[event_text]["causes"].append(cause)
            result = ev.get("result", "").strip()
            if result and result not in index[event_text]["results"]:
                index[event_text]["results"].append(result)
    return dict(sorted(index.items(), key=lambda x: x[1]["count"], reverse=True))


def build_relationship_index(canon_map: dict[str, dict]) -> dict:
    """
    从 canon relationships 字段构建关系索引。
    键为 "人物A|人物B"（字典序排列保证唯一性）。
    返回 {pair_key: {count, chunks, person_a, person_b, interactions}}
    """
    index: dict = {}
    for cid, rec in canon_map.items():
        for rel in rec.get("relationships", []):
            if not isinstance(rel, dict):
                continue
            pa = rel.get("person_a", "").strip()
            pb = rel.get("person_b", "").strip()
            if not pa or not pb:
                continue
            # 统一排序保证 A|B 和 B|A 合并为同一条
            pair = "|".join(sorted([pa, pb]))
            if pair not in index:
                index[pair] = {
                    "count": 0,
                    "chunks": [],
                    "person_a": sorted([pa, pb])[0],
                    "person_b": sorted([pa, pb])[1],
                    "interactions": [],
                }
            index[pair]["count"] += 1
            if cid not in index[pair]["chunks"]:
                index[pair]["chunks"].append(cid)
            interaction = rel.get("interaction", "").strip()
            if interaction and interaction not in index[pair]["interactions"]:
                index[pair]["interactions"].append(interaction)
    return dict(sorted(index.items(), key=lambda x: x[1]["count"], reverse=True))


def build_style_summary(style_map: dict[str, dict]) -> dict:
    """汇总风格标签统计、叙事语气分布、对话密度分布。"""
    tag_counts: dict[str, int] = defaultdict(int)
    tone_dist:  dict[str, int] = defaultdict(int)
    density_dist: dict[str, int] = defaultdict(int)

    for rec in style_map.values():
        for tag in rec.get("style_tags", []):
            if isinstance(tag, str) and tag.strip():
                tag_counts[tag.strip()] += 1

        tone = rec.get("narration_tone", "").strip()
        if tone:
            tone_dist[tone] += 1

        density = rec.get("dialogue_density", "").strip()
        if density:
            density_dist[density] += 1

    return {
        "total_chunks_with_style": len(style_map),
        "tag_counts": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)),
        "tone_distribution": dict(sorted(tone_dist.items(), key=lambda x: x[1], reverse=True)),
        "dialogue_density_distribution": dict(density_dist),
    }


# ── prompt_context.md 生成 ────────────────────────────────────────────────────

def generate_prompt_context(merged_chunks: list[dict]) -> str:
    lines = []
    lines.append("# 知识库上下文")
    lines.append(f"\n> 生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 共 {len(merged_chunks)} 个片段\n")
    lines.append("---\n")

    for entry in merged_chunks:
        chunk_id     = entry.get("chunk_id", "")
        chapter_hint = entry.get("chapter_hint", "")
        char_start   = entry.get("char_start", "")
        char_end     = entry.get("char_end", "")
        canon        = entry.get("canon") or {}
        style        = entry.get("style") or {}

        lines.append(f"## [{chunk_id}] {chapter_hint}")
        lines.append(f"**位置**：字符 {char_start}–{char_end}")

        # 摘要
        summary = canon.get("summary", "")
        if summary:
            lines.append(f"**摘要**：{summary}")

        # 人物行为
        characters = canon.get("characters", [])
        if characters:
            lines.append("**人物行为**：")
            for char in characters:
                if isinstance(char, dict):
                    name    = char.get("name", "")
                    action  = char.get("action", "")
                    emotion = char.get("emotion", "")
                    lines.append(f"- {name}：{action}（{emotion}）")

        # 人物关系互动
        relationships = canon.get("relationships", [])
        if relationships:
            lines.append("**关系互动**：")
            for rel in relationships:
                if isinstance(rel, dict):
                    pa = rel.get("person_a", "")
                    pb = rel.get("person_b", "")
                    interaction = rel.get("interaction", "")
                    lines.append(f"- {pa} × {pb}：{interaction}")

        # 地点 / 时间
        locations    = canon.get("locations", [])
        time_markers = canon.get("time_markers", [])
        if locations:
            lines.append(f"**地点**：{', '.join(locations)}")
        if time_markers:
            lines.append(f"**时间**：{', '.join(time_markers)}")

        # 风格标注
        narration_tone    = style.get("narration_tone", "")
        dialogue_density  = style.get("dialogue_density", "")
        style_tags        = style.get("style_tags", [])
        if narration_tone or dialogue_density or style_tags:
            style_parts = []
            if narration_tone:
                style_parts.append(f"语气：{narration_tone}")
            if dialogue_density:
                style_parts.append(f"对话密度：{dialogue_density}")
            if style_tags:
                style_parts.append(f"标签：{' / '.join(style_tags)}")
            lines.append(f"**风格**：{' | '.join(style_parts)}")

        lines.append("")  # 空行分隔

    return "\n".join(lines)


# ── 主函数 ───────────────────────────────────────────────────────────────────

def main() -> None:
    canon_map = load_dir(CANON_DIR)
    style_map = load_dir(STYLE_DIR)

    if not canon_map and not style_map:
        print("outputs/canon/ 和 outputs/style/ 均为空，请先运行提取脚本。")
        sys.exit(0)

    print(f"读取 canon：{len(canon_map)} 条  |  style：{len(style_map)} 条")

    merged_chunks = merge_records(canon_map, style_map)
    print(f"合并后共 {len(merged_chunks)} 个 chunk，开始生成知识库...")

    # 1. master_kb.json
    master_kb = {
        "generated_at":   datetime.datetime.now().isoformat(),
        "total_chunks":   len(merged_chunks),
        "canon_count":    len(canon_map),
        "style_count":    len(style_map),
        "chunks":         merged_chunks,
    }
    with open(MASTER_KB_PATH, "w", encoding="utf-8") as f:
        json.dump(master_kb, f, ensure_ascii=False, indent=2)
    print(f"已写出：{MASTER_KB_PATH}")

    # 2. prompt_context.md
    md_content = generate_prompt_context(merged_chunks)
    with open(PROMPT_CONTEXT_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"已写出：{PROMPT_CONTEXT_PATH}")

    # 3. character_index.json（含行为/情绪汇总）
    char_idx = build_character_index(canon_map)
    with open(CHARACTER_IDX_PATH, "w", encoding="utf-8") as f:
        json.dump(char_idx, f, ensure_ascii=False, indent=2)
    print(f"已写出：{CHARACTER_IDX_PATH}（{len(char_idx)} 个人物）")

    # 4. location_index.json
    loc_idx = build_location_index(canon_map)
    with open(LOCATION_IDX_PATH, "w", encoding="utf-8") as f:
        json.dump(loc_idx, f, ensure_ascii=False, indent=2)
    print(f"已写出：{LOCATION_IDX_PATH}（{len(loc_idx)} 个地点）")

    # 5. event_index.json
    ev_idx = build_event_index(canon_map)
    with open(EVENT_IDX_PATH, "w", encoding="utf-8") as f:
        json.dump(ev_idx, f, ensure_ascii=False, indent=2)
    print(f"已写出：{EVENT_IDX_PATH}（{len(ev_idx)} 个事件）")

    # 6. relationship_index.json（新增）
    rel_idx = build_relationship_index(canon_map)
    with open(RELATIONSHIP_IDX_PATH, "w", encoding="utf-8") as f:
        json.dump(rel_idx, f, ensure_ascii=False, indent=2)
    print(f"已写出：{RELATIONSHIP_IDX_PATH}（{len(rel_idx)} 对关系）")

    # 7. style_summary.json（新增）
    style_sum = build_style_summary(style_map)
    with open(STYLE_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(style_sum, f, ensure_ascii=False, indent=2)
    print(f"已写出：{STYLE_SUMMARY_PATH}")

    print(f"\n汇总完成！知识库目录：{KB_DIR}")


if __name__ == "__main__":
    main()
