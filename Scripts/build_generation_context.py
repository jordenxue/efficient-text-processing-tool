"""
build_generation_context.py — 生成层最小上下文包构建器
用法：
  python Scripts/build_generation_context.py 江涵 --mode continue_writing
  python Scripts/build_generation_context.py 江涵 --mode rewrite --source-text "原始片段..."
  python Scripts/build_generation_context.py 涵宝 --mode continue_writing --appearances 3
  python Scripts/build_generation_context.py 江涵 --mode rewrite --source-file path/to/text.txt

设计说明：

【为什么续写和改写共用同一个 context builder】
  续写和改写所需的人物事实、关系候选、地点候选、风格提示是完全相同的——
  它们描述的是同一个世界和人物状态。mode 差异只体现在最终任务说明上。
  若写两套 context builder，只会产生维护负担，且容易出现字段语义漂移。

【为什么这次不做 role-play 系统】
  role-play 是多轮有状态的交互系统，需要会话管理、角色扮演框架和状态回写机制。
  本脚本只生成一次性上下文包，供上层模型单次消费，定位完全不同。
  role-play 是下一步，不在本轮范围。

【为什么不改 query.py 的 --json 合同】
  query.py 的 --json 输出面向 CLI 脚本消费，字段已经稳定，其他工具可能依赖该合同。
  generation context 是新的消费层，字段语义不同（如增加 mode、source_text、style_guidance 等），
  强行合并会让两个用途的字段耦合在一起，反而降低可读性和稳定性。

【为什么 relationship/location 这里只作为候选，而不是高置信事实】
  这两个索引来自 chunk 级共现聚合，不是人工核验的叙事事实。
  同一 chunk 里出现两个人物，不等于他们有直接互动；同一 chunk 里提到一个地点，
  不等于人物在那里。写成"候选"而不是"事实"，是对数据来源的如实表达。

【为什么 style 目前只做占位，而不伪装成完整自动风格管线】
  当前没有稳定的自动风格来源：style 抽取管线尚未接入 query 层，
  且 9 个 hard holes 已归档但未完全覆盖。伪装成"已接入风格"会误导生成层，
  产生幻觉式风格控制。占位字段让下游消费者知道"这里将来可以放风格说明"，
  但不会带来错误预期。
"""

import os
import sys
import json
import argparse
from datetime import datetime

# ── 路径基准 ──────────────────────────────────────────────────────────────────
# 路径常量集中定义于 paths.py（三层资产索引），此处统一导入。
# 若需调整目录结构，只改 paths.py，不需要逐脚本搜替。
import paths as _p

BASE_DIR    = _p.BASE_DIR
SCRIPTS_DIR = _p.SCRIPTS_DIR
OUTPUT_DIR  = _p.OUTPUTS_DIR

# 将 Scripts 目录加入路径，以便直接复用 query.py 中已冻结的函数，
# 而不是重新实现一套等价但容易漂移的逻辑。
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from query import (
    resolve_person_query,
    load_character_profiles_v2,
    load_character_query_aliases_v2,
    load_character_appearance_samples,
    build_relationship_candidates,
    build_location_candidates,
)

VALID_MODES = ("continue_writing", "rewrite")


def load_prompt_prefix_from_file(path: str) -> str:
    """
    只从外部文件读取可选的 prompt 顶部前置文本。
    这样第一轮 A/B 的唯一变量就是“是否注入同一段守则”，
    不需要把守则硬编码到 builder 主逻辑里。
    """
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def prepend_prompt_prefix(prompt_body: str, prompt_prefix: str) -> str:
    """
    只在最终 prompt 文本层插入前置守则。
    这里不改 context JSON 的事实内容，确保 A 版基线保持不变，
    B 版只是多一个可控的顶部提示块。
    """
    prompt_prefix = prompt_prefix.strip()
    if not prompt_prefix:
        return prompt_body
    return f"{prompt_prefix}\n\n{prompt_body}"


# ── 1. 人物查询解析 ────────────────────────────────────────────────────────────

def resolve_character_context(query: str) -> dict:
    """
    通过 query.py 的既有解析路径（canonical -> observed_alias -> query_alias）
    命中人物，返回供 context builder 使用的解析摘要。
    不重新实现解析逻辑，保持与 query.py 行为严格一致。
    """
    profiles = load_character_profiles_v2()
    query_aliases = load_character_query_aliases_v2()
    resolved = resolve_person_query(query, profiles=profiles, query_aliases=query_aliases)

    if not resolved:
        return {
            "matched": False,
            "query": query,
            "canonical_name": None,
            "match_type": None,
            "observed_aliases": [],
            "query_alias_input": None,
            "profile": None,
        }

    profile = resolved["profile"]
    match_type = resolved["matched_by"]
    canonical_name = resolved["canonical_name"]

    return {
        "matched": True,
        "query": query,
        "canonical_name": canonical_name,
        "match_type": match_type,
        "observed_aliases": profile.get("aliases", []),
        "query_alias_input": query if match_type == "query_alias" else None,
        "profile": profile,
    }


# ── 2. appearance 样本收集 ─────────────────────────────────────────────────────

def collect_appearance_samples(canonical_name: str, limit: int = 3) -> list[dict]:
    """
    复用 query.py 的 appearance 抽样函数。
    limit 首版默认取 3，不要过大，避免 context 包膨胀。
    """
    if not canonical_name or limit <= 0:
        return []
    return load_character_appearance_samples(canonical_name, limit)


# ── 3. 关系候选收集 ────────────────────────────────────────────────────────────

def collect_relationship_candidates(canonical_name: str, max_items: int = 3) -> list[dict]:
    """
    复用 query.py 的 build_relationship_candidates。
    结果仍标注为"候选"语义：来自 chunk 共现聚合，不是人工核验的事实。
    """
    if not canonical_name:
        return []
    return build_relationship_candidates(canonical_name, max_items=max_items)


# ── 4. 地点候选收集 ────────────────────────────────────────────────────────────

def collect_location_candidates(profile: dict, max_items: int = 3) -> list[dict]:
    """
    复用 query.py 的 build_location_candidates。
    结果同样只是候选：人物 appearance chunk 与地点索引的共现聚合，不代表高置信叙事事实。
    """
    if not profile:
        return []
    return build_location_candidates(profile, max_items=max_items)


# ── 5. 主 context builder ──────────────────────────────────────────────────────

def build_generation_context(
    query: str,
    mode: str,
    source_text: str = "",
    appearance_limit: int = 3,
    rel_limit: int = 3,
    loc_limit: int = 3,
) -> dict:
    """
    两种 mode（continue_writing / rewrite）共用同一套 context builder。
    这是本脚本的核心设计原则：上下文事实层完全相同，mode 差异只影响任务说明层。

    输出字段说明：
      mode                  当前任务模式
      query                 原始查询词
      resolved_character    query resolution 摘要（命中方式、canonical 名称、别名层）
      query_resolution      解析过程说明（文字摘要，供生成层参考）
      appearance_samples    少量 appearance 证据样本
      relationship_candidates  关系候选列表（候选，非高置信事实）
      location_candidates   地点候选列表（候选，非高置信事实）
      style_guidance        风格占位字段（当前无稳定自动来源，内含说明）
      source_text           仅 rewrite 模式携带的待改写原文片段
      notes                 构建说明与警告
    """
    if mode not in VALID_MODES:
        raise ValueError(f"mode 必须为 {VALID_MODES} 之一，当前为: {mode!r}")

    char_ctx = resolve_character_context(query)
    canonical_name = char_ctx.get("canonical_name")
    profile = char_ctx.get("profile") or {}

    if char_ctx["matched"]:
        appearances = collect_appearance_samples(canonical_name, appearance_limit)
        rel_candidates = collect_relationship_candidates(canonical_name, rel_limit)
        loc_candidates = collect_location_candidates(profile, loc_limit)
        query_resolution = _build_resolution_notes(char_ctx)
    else:
        appearances = []
        rel_candidates = []
        loc_candidates = []
        query_resolution = "查询未命中任何人物（canonical / observed_alias / query_alias 三层均未匹配）。"

    # 风格占位：目前 style 管线尚未接入生成层。
    # 下游消费者可手动填入风格说明，或等待 style 管线稳定后替换此字段。
    style_guidance = {
        "status": "placeholder",
        "note": (
            "当前无稳定自动风格来源。style 抽取管线存在 9 个 hard holes，"
            "且尚未正式接入生成层消费路径。"
            "如需风格控制，请在此字段手动填入风格说明，或留空。"
        ),
        "manual_style_hint": "",
    }

    notes = [
        "本 context 包由 build_generation_context.py 生成，仅供生成层单次消费使用。",
        "relationship_candidates 和 location_candidates 均为 chunk 共现候选，不是高置信叙事事实。",
        "event 未实现（当前 event 索引噪音较大，暂不纳入 context 包）。",
        f"生成时间: {datetime.now().isoformat()}",
    ]

    ctx: dict = {
        "mode": mode,
        "query": query,
        "resolved_character": {
            "matched": char_ctx["matched"],
            "canonical_name": canonical_name,
            "match_type": char_ctx["match_type"],
            "observed_aliases": char_ctx["observed_aliases"],
            "query_alias_input": char_ctx["query_alias_input"],
            "mention_count": profile.get("mention_count", 0),
            "first_chunk": profile.get("first_chunk"),
            "last_chunk": profile.get("last_chunk"),
        },
        "query_resolution": query_resolution,
        "appearance_samples": appearances,
        "relationship_candidates": rel_candidates,
        "location_candidates": loc_candidates,
        "style_guidance": style_guidance,
        "source_text": source_text if mode == "rewrite" else "",
        "notes": notes,
    }

    return ctx


def _build_resolution_notes(char_ctx: dict) -> str:
    """
    生成人物解析过程的文字摘要，供生成层了解命中方式。
    解析顺序固定为 canonical -> observed_alias -> query_alias，与 query.py 保持一致。
    """
    match_type = char_ctx["match_type"]
    query = char_ctx["query"]
    canonical = char_ctx["canonical_name"]

    if match_type == "canonical":
        return f'查询词 [{query}] 直接命中 canonical 名称。'
    elif match_type == "observed_alias":
        return (
            f'查询词 [{query}] 通过 observed_alias 命中，'
            f'resolved canonical 为 [{canonical}]。'
            f'该别名已在 appearances/raw_name 层真实出现过。'
        )
    elif match_type == "query_alias":
        return (
            f'查询词 [{query}] 通过 query_alias 命中，'
            f'resolved canonical 为 [{canonical}]。'
            f'该名字仅作为 query-time 支持，未进入 observed aliases 事实层。'
        )
    return "未知命中方式。"


# ── 6. 续写 prompt 渲染 ────────────────────────────────────────────────────────

def render_continue_writing_prompt(ctx: dict) -> str:
    """
    将 context 包渲染成适合续写任务的 prompt/context 文本。
    重点：
      - 告知上层模型：人物是谁、已知候选关系/地点、appearance 证据
      - 任务要求续写，不要与已有设定冲突
    """
    lines = [
        "=== 续写任务上下文 ===",
        "",
        "【任务说明】",
        "请在以下已知人物、关系、地点约束下，继续向前续写。",
        "不要与已有角色关系、地点线索或人物行为模式明显冲突。",
        "如果下方提供了风格提示，请保持风格方向一致。",
        "",
    ]

    _append_character_section(lines, ctx)
    _append_appearance_section(lines, ctx)
    _append_relationship_section(lines, ctx)
    _append_location_section(lines, ctx)
    _append_style_section(lines, ctx)

    lines += [
        "",
        "【续写要求】",
        "- 在上述人物状态与世界约束下向前写",
        "- 保持人物性格、关系与地点信息的内部一致",
        "- 不随意引入与已有知识库矛盾的新设定",
        "- 写作语言：中文",
        "",
        "【注意】",
        "- relationship_candidates 和 location_candidates 均为候选，非高置信事实",
        "- event 当前未接入，请不要依赖事件索引作为续写依据",
        "- style_guidance 当前为占位字段，如为空请自行判断风格",
    ]

    return "\n".join(lines)


# ── 7. 改写 prompt 渲染 ────────────────────────────────────────────────────────

def render_rewrite_prompt(ctx: dict) -> str:
    """
    将 context 包渲染成适合改写任务的 prompt/context 文本。
    比续写多一个核心要求：基于输入片段改写，保留已知约束。
    如果输入片段与知识库冲突，默认提醒以知识库设定为准。
    """
    lines = [
        "=== 改写任务上下文 ===",
        "",
        "【任务说明】",
        "请基于下方【待改写原文】进行改写。",
        "优先保留已知人物、关系、地点约束，重写表达，不随意篡改核心事实。",
        "如果待改写片段与下方知识库信息存在冲突，以知识库设定为默认优先。",
        "",
    ]

    # 改写模式的核心：先展示待改写原文
    source_text = ctx.get("source_text", "").strip()
    lines.append("【待改写原文】")
    if source_text:
        lines.append(source_text)
    else:
        lines.append("（未提供待改写原文，请手动补充）")
    lines.append("")

    _append_character_section(lines, ctx)
    _append_appearance_section(lines, ctx)
    _append_relationship_section(lines, ctx)
    _append_location_section(lines, ctx)
    _append_style_section(lines, ctx)

    lines += [
        "",
        "【改写要求】",
        "- 重写表达，不保留原文逐字句式",
        "- 不改变人物身份、核心关系、地点等已知事实",
        "- 如原文与知识库候选信息有明显矛盾，改写时以知识库设定为准",
        "- 写作语言：中文",
        "",
        "【注意】",
        "- relationship_candidates 和 location_candidates 均为候选，非高置信事实",
        "- event 当前未接入，请不要依赖事件索引",
        "- style_guidance 当前为占位字段，如为空请自行判断风格",
    ]

    return "\n".join(lines)


# ── 共用辅助：渲染各区块 ────────────────────────────────────────────────────────

def _append_character_section(lines: list[str], ctx: dict) -> None:
    rc = ctx.get("resolved_character", {})
    lines.append("【人物信息】")
    if not rc.get("matched"):
        lines.append("  未命中任何人物，以下区块可能为空。")
        lines.append("")
        return

    lines.append(f"  canonical 名称: {rc.get('canonical_name') or '（无）'}")
    lines.append(f"  命中方式: {rc.get('match_type') or '（无）'}")

    obs = rc.get("observed_aliases", [])
    lines.append(f"  observed aliases: {('、'.join(obs)) if obs else '（无）'}")

    qa_input = rc.get("query_alias_input")
    if qa_input:
        lines.append(f"  query_alias_input: {qa_input}（仅 query-time，未进入事实层）")

    lines.append(f"  解析说明: {ctx.get('query_resolution', '')}")
    lines.append(f"  出现次数: {rc.get('mention_count', 0)}")
    lines.append(f"  首次出现 chunk: {rc.get('first_chunk') or '（无）'}")
    lines.append(f"  末次出现 chunk: {rc.get('last_chunk') or '（无）'}")
    lines.append("")


def _append_appearance_section(lines: list[str], ctx: dict) -> None:
    samples = ctx.get("appearance_samples", [])
    lines.append("【appearance 证据样本】（少量，用于核查人物行为与称谓）")
    if not samples:
        lines.append("  （无）")
        lines.append("")
        return

    for i, s in enumerate(samples, 1):
        chunk_id = s.get("chunk_id") or "（未知）"
        chapter = s.get("chapter_hint") or "（无章节提示）"
        lines.append(f"  {i}. {chunk_id} | {chapter}")
        lines.append(f"     raw_name: {s.get('raw_name') or '（无）'}")
        lines.append(f"     action: {s.get('action') or '（无）'}")
        lines.append(f"     emotion: {s.get('emotion') or '（无）'}")
    lines.append("")


def _append_relationship_section(lines: list[str], ctx: dict) -> None:
    candidates = ctx.get("relationship_candidates", [])
    lines.append("【关系候选】（chunk 共现聚合，仅供参考，非高置信事实）")
    if not candidates:
        lines.append("  （无）")
        lines.append("")
        return

    for i, item in enumerate(candidates, 1):
        person = item.get("related_person") or "（未知）"
        count = item.get("overlap_chunk_count", 0)
        interaction = item.get("interaction_sample") or "（无摘要）"
        lines.append(f"  {i}. {person} | 关联 chunk 数: {count}")
        lines.append(f"     互动摘要: {interaction}")
    lines.append("")


def _append_location_section(lines: list[str], ctx: dict) -> None:
    candidates = ctx.get("location_candidates", [])
    lines.append("【地点候选】（chunk 共现聚合，仅供参考，非高置信事实）")
    if not candidates:
        lines.append("  （无）")
        lines.append("")
        return

    for i, item in enumerate(candidates, 1):
        loc = item.get("location_name") or "（未知）"
        count = item.get("overlap_chunk_count", 0)
        lines.append(f"  {i}. {loc} | 共现 chunk 数: {count}")
    lines.append("")


def _append_style_section(lines: list[str], ctx: dict) -> None:
    sg = ctx.get("style_guidance", {})
    lines.append("【风格说明】")
    if sg.get("status") == "placeholder":
        lines.append(f"  （占位）{sg.get('note', '')}")
        hint = sg.get("manual_style_hint", "").strip()
        if hint:
            lines.append(f"  手动风格提示: {hint}")
    else:
        hint = sg.get("manual_style_hint", "").strip()
        lines.append(f"  {hint if hint else '（无风格提示）'}")
    lines.append("")


# ── 8. 输出保存 ────────────────────────────────────────────────────────────────

def save_outputs(ctx: dict, output_dir: str, prompt_prefix: str = "") -> dict[str, str]:
    """
    保存两类输出：
      1. 结构化 context 包（JSON）—— 始终保存
      2. 与 mode 对应的 prompt 文本（txt）—— 按 mode 分流，只保存对应的一份

    mode=continue_writing -> 只保存 continue_writing prompt
    mode=rewrite          -> 只保存 rewrite prompt
    两种 mode 不交叉输出，确保调用方拿到的文件与请求的任务类型一致。
    """
    os.makedirs(output_dir, exist_ok=True)

    mode = ctx["mode"]
    canonical = ctx["resolved_character"].get("canonical_name") or ctx["query"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = canonical.replace("/", "_").replace("\\", "_")

    paths: dict[str, str] = {}

    # JSON context 包（两种 mode 都保存，是共用 context builder 产物的完整记录）
    json_path = os.path.join(output_dir, f"gen_ctx_{safe_name}_{mode}_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ctx, f, ensure_ascii=False, indent=2)
    paths["context_json"] = json_path

    # 按 mode 只产出对应的 prompt，不产出另一个 mode 的 prompt
    if mode == "continue_writing":
        cw_text = prepend_prompt_prefix(render_continue_writing_prompt(ctx), prompt_prefix)
        cw_path = os.path.join(output_dir, f"gen_ctx_{safe_name}_continue_writing_{ts}.txt")
        with open(cw_path, "w", encoding="utf-8") as f:
            f.write(cw_text)
        paths["continue_writing_prompt"] = cw_path
    elif mode == "rewrite":
        rw_text = prepend_prompt_prefix(render_rewrite_prompt(ctx), prompt_prefix)
        rw_path = os.path.join(output_dir, f"gen_ctx_{safe_name}_rewrite_{ts}.txt")
        with open(rw_path, "w", encoding="utf-8") as f:
            f.write(rw_text)
        paths["rewrite_prompt"] = rw_path

    return paths


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="构建续写/改写共用生成上下文包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python Scripts/build_generation_context.py 江涵 --mode continue_writing
  python Scripts/build_generation_context.py 涵宝 --mode rewrite --source-text "她抬起头，看向窗外..."
  python Scripts/build_generation_context.py 江涵 --mode continue_writing --appearances 5
""",
    )
    parser.add_argument("query", help="人物查询词（必需）")
    parser.add_argument(
        "--mode",
        required=True,
        choices=list(VALID_MODES),
        help="任务模式：continue_writing（续写）或 rewrite（改写）",
    )
    parser.add_argument(
        "--source-text",
        default="",
        metavar="TEXT",
        help="待改写的源文本片段（仅 rewrite 模式有意义）",
    )
    parser.add_argument(
        "--source-file",
        default="",
        metavar="FILE",
        help="从文件读取待改写源文本（与 --source-text 互斥，仅 rewrite 模式有意义）",
    )
    parser.add_argument(
        "--appearances",
        type=int,
        default=3,
        metavar="N",
        help="附带前 N 条 appearance 样本（默认 3）",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        metavar="DIR",
        help="输出目录（默认 outputs/generation/）",
    )
    parser.add_argument(
        "--prompt-prefix-file",
        default="",
        metavar="FILE",
        help="可选的 prompt 顶部前置文本文件；仅影响最终 prompt 文本，不改 context JSON",
    )

    args = parser.parse_args()

    # 处理 source_text
    source_text = args.source_text
    if args.source_file:
        if args.source_text:
            print("警告：--source-text 与 --source-file 同时提供，将使用 --source-file 的内容。")
        try:
            with open(args.source_file, encoding="utf-8") as f:
                source_text = f.read()
        except OSError as e:
            print(f"错误：无法读取 --source-file: {e}")
            sys.exit(1)

    # rewrite 模式前置校验：source_text 不能为空。
    # 两者均为空时直接报错退出，不生成占位 prompt，避免实验数据静默失效。
    if args.mode == "rewrite" and not source_text.strip():
        print("错误：rewrite 模式必须提供待改写原文（--source-text TEXT 或 --source-file FILE），两者均为空。")
        sys.exit(1)

    try:
        prompt_prefix = load_prompt_prefix_from_file(args.prompt_prefix_file)
    except OSError as e:
        print(f"错误：无法读取 --prompt-prefix-file: {e}")
        sys.exit(1)

    output_dir = args.output_dir if args.output_dir else os.path.join(OUTPUT_DIR, "generation")

    print(f"[build_generation_context] query={args.query!r} mode={args.mode}")
    if args.prompt_prefix_file:
        print(f"  prompt_prefix_file={args.prompt_prefix_file}")

    ctx = build_generation_context(
        query=args.query,
        mode=args.mode,
        source_text=source_text,
        appearance_limit=args.appearances,
    )

    matched = ctx["resolved_character"]["matched"]
    canonical = ctx["resolved_character"].get("canonical_name")
    print(f"  人物命中: {'是' if matched else '否'} | canonical={canonical}")

    paths = save_outputs(ctx, output_dir, prompt_prefix=prompt_prefix)

    print("\n[输出文件]")
    for label, path in paths.items():
        print(f"  {label}: {path}")

    if not matched:
        print("\n警告：人物未命中，context 包中人物相关字段为空。请确认查询词是否正确。")
        sys.exit(1)


if __name__ == "__main__":
    main()
