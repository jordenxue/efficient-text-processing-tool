"""
query.py — 查询知识库
用法：
  python Scripts/query.py 江涵
  python Scripts/query.py --list characters
  python Scripts/query.py --search "关键词"
"""

import os
import sys
import json
import argparse
from functools import lru_cache

# ── 路径基准 ─────────────────────────────────────────────────────────────────
# 路径常量集中定义于 paths.py（三层资产索引），此处统一导入。
# 若需调整目录结构，只改 paths.py，不需要逐脚本搜替。
import paths as _p

BASE_DIR = _p.BASE_DIR

MASTER_KB_PATH                = _p.KB_MASTER
CHARACTER_IDX_PATH            = _p.KB_CHARACTER_INDEX_LEGACY
CHARACTER_PROFILES_V2_PATH    = _p.KB_PROFILES_V2
CHARACTER_APPEARANCES_V2_PATH = _p.KB_APPEARANCES_V2
CHARACTER_QUERY_ALIASES_V2_PATH = _p.KB_QUERY_ALIASES_V2
RELATIONSHIP_IDX_PATH         = _p.KB_RELATIONSHIP
LOCATION_IDX_PATH             = _p.KB_LOCATION
EVENT_IDX_PATH                = _p.KB_EVENT
CHUNKS_DIR                    = _p.CHUNKS_DIR

INDEX_MAP = {
    "characters": CHARACTER_IDX_PATH,
    "locations": LOCATION_IDX_PATH,
    "events": EVENT_IDX_PATH,
}

SEARCH_FIELDS = ["chunk_id", "summary", "characters", "events", "locations", "time_markers", "chapter_hint"]

MATCH_TYPE_DISPLAY = {
    "canonical": "canonical（直接命中）",
    "observed_alias": "observed_alias（已观察别名）",
    "query_alias": "query_alias（仅 query-time 命中）",
}

SECTION_TYPE_DISPLAY = {
    "front_matter": "[front_matter]",
    "in_universe_document": "[in_universe_document]",
    "setting_exposition": "[setting_exposition]",
    "author_meta": "[author_meta]",
}


# ── 加载 ──────────────────────────────────────────────────────────────────────

def load_json_file(path: str, default):
    if not os.path.isfile(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_master_kb() -> list[dict]:
    if not os.path.isfile(MASTER_KB_PATH):
        print(f"错误：知识库文件不存在：{MASTER_KB_PATH}")
        print("请先运行：python Scripts/merge.py")
        sys.exit(1)
    data = load_json_file(MASTER_KB_PATH, {})
    return data.get("chunks", [])


def load_index(field: str) -> dict:
    path = INDEX_MAP.get(field)
    if not path or not os.path.isfile(path):
        return {}
    return load_json_file(path, {})


def load_character_profiles_v2() -> dict:
    profiles = load_json_file(CHARACTER_PROFILES_V2_PATH, {})
    if not isinstance(profiles, dict):
        return {}
    return profiles


def load_character_query_aliases_v2() -> dict:
    aliases = load_json_file(CHARACTER_QUERY_ALIASES_V2_PATH, {})
    if not isinstance(aliases, dict):
        return {}
    return aliases


@lru_cache(maxsize=1)
def load_relationship_index() -> dict:
    index = load_json_file(RELATIONSHIP_IDX_PATH, {})
    if not isinstance(index, dict):
        return {}
    return index


@lru_cache(maxsize=1)
def load_location_index() -> dict:
    index = load_json_file(LOCATION_IDX_PATH, {})
    if not isinstance(index, dict):
        return {}
    return index


@lru_cache(maxsize=4096)
def load_chunk_meta(chunk_id: str) -> dict:
    if not chunk_id:
        return {}

    meta_path = os.path.join(CHUNKS_DIR, f"{chunk_id}.meta.json")
    if not os.path.isfile(meta_path):
        return {}

    meta = load_json_file(meta_path, {})
    if not isinstance(meta, dict):
        return {}
    return meta


def load_character_appearance_samples(canonical_name: str, limit: int) -> list[dict]:
    # appearance 是证据层，和 profile 摘要层分开保存；这里只做抽样，避免 CLI 一次性吐出整本书的全部记录。
    if limit <= 0 or not os.path.isfile(CHARACTER_APPEARANCES_V2_PATH):
        return []

    samples: list[dict] = []
    with open(CHARACTER_APPEARANCES_V2_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("canonical_name") != canonical_name:
                continue

            samples.append({
                "chunk_id": record.get("chunk_id"),
                "raw_name": record.get("raw_name"),
                "canonical_name": record.get("canonical_name"),
                "alias_source": record.get("alias_source"),
                "action": record.get("action"),
                "emotion": record.get("emotion"),
                "chapter_hint": record.get("chapter_hint"),
            })
            if len(samples) >= limit:
                break

    return samples


def format_inline_values(values: list[str]) -> str:
    cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if not cleaned:
        return "（无）"
    return "、".join(cleaned)


def append_ranked_lines(lines: list[str], title: str, items: list[str], max_items: int = 5) -> None:
    lines.append(f"{title}:")

    cleaned = [item.strip() for item in items if isinstance(item, str) and item.strip()]
    if not cleaned:
        lines.append("  （无）")
        return

    for index, item in enumerate(cleaned[:max_items], 1):
        lines.append(f"  {index}. {item}")
    if len(cleaned) > max_items:
        lines.append(f"  ... 还有 {len(cleaned) - max_items} 条")


def get_section_type_display_tag(chunk_id: str) -> str | None:
    # section_type 这里只用于提示样本来自哪类 chunk，不能改变证据选取或事实层含义。
    section_type = load_chunk_meta(chunk_id).get("section_type")
    if not isinstance(section_type, str) or not section_type or section_type == "story_scene":
        return None
    return SECTION_TYPE_DISPLAY.get(section_type, f"[{section_type}]")


def normalize_chunk_ids(chunks: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for chunk_id in chunks:
        if not isinstance(chunk_id, str):
            continue
        cleaned = chunk_id.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def format_evidence_chunk(chunk_id: str | None) -> tuple[str, bool]:
    cleaned = chunk_id.strip() if isinstance(chunk_id, str) else ""
    if not cleaned:
        return "（无）", False

    # section_type 这里只用于证据展示提醒，不能参与过滤、排序或事实重判。
    section_tag = get_section_type_display_tag(cleaned)
    if section_tag:
        return f"{cleaned} {section_tag}", True
    return cleaned, False


def build_relationship_candidates(canonical_name: str, max_items: int = 3) -> list[dict]:
    # 首版轻量联动只做 relationship + location。relationship 索引已具备人物对与互动摘要，
    # 而 event 当前基本是一次性条目，直接挂默认输出会很噪，所以本版明确不实现 event。
    grouped: dict[str, dict] = {}
    for key, info in load_relationship_index().items():
        if not isinstance(info, dict):
            continue

        person_a = info.get("person_a")
        person_b = info.get("person_b")
        if person_a == canonical_name:
            related_person = person_b
        elif person_b == canonical_name:
            related_person = person_a
        elif isinstance(key, str) and canonical_name in key:
            parts = [part.strip() for part in key.split("|") if part.strip()]
            related_person = next((part for part in parts if part != canonical_name), None)
        else:
            continue

        if not isinstance(related_person, str) or not related_person.strip():
            continue

        chunks = normalize_chunk_ids(info.get("chunks", []))
        interactions = [
            item.strip()
            for item in info.get("interactions", [])
            if isinstance(item, str) and item.strip()
        ]
        overlap_chunk_count = len(chunks) or int(info.get("count", 0) or 0)
        if overlap_chunk_count <= 0:
            continue

        related_person = related_person.strip()
        bucket = grouped.setdefault(related_person, {
            "related_person": related_person,
            "chunks": [],
            "interaction_sample": None,
        })
        bucket["chunks"] = normalize_chunk_ids(bucket["chunks"] + chunks)
        if bucket["interaction_sample"] is None and interactions:
            bucket["interaction_sample"] = interactions[0]

    candidates: list[dict] = []
    for related_person, info in grouped.items():
        chunks = info.get("chunks", [])
        if not chunks:
            continue
        candidates.append({
            "related_person": related_person,
            "overlap_chunk_count": len(chunks),
            "interaction_sample": info.get("interaction_sample"),
            "sample_chunk_id": chunks[0],
        })

    candidates.sort(key=lambda item: (-item["overlap_chunk_count"], item["related_person"]))
    return candidates[:max_items]


def build_location_candidates(profile: dict, max_items: int = 3) -> list[dict]:
    # location 联动只做人物 appearance chunk 与地点索引的共现聚合；输出文案必须写成候选，
    # 避免把 chunk 级共现误导成高置信事实地点。
    profile_chunks = normalize_chunk_ids(profile.get("chunk_ids", []))
    if not profile_chunks:
        return []

    profile_chunk_set = set(profile_chunks)
    candidates: list[dict] = []
    for location_name, info in load_location_index().items():
        if not isinstance(location_name, str) or not location_name.strip() or not isinstance(info, dict):
            continue

        overlap_chunks = [
            chunk_id for chunk_id in normalize_chunk_ids(info.get("chunks", []))
            if chunk_id in profile_chunk_set
        ]
        if not overlap_chunks:
            continue

        candidates.append({
            "location_name": location_name.strip(),
            "overlap_chunk_count": len(overlap_chunks),
            "sample_chunk_id": overlap_chunks[0],
        })

    candidates.sort(key=lambda item: (-item["overlap_chunk_count"], item["location_name"]))
    return candidates[:max_items]


def build_person_display_notes(match_type: str | None) -> list[str]:
    notes = [
        "解析顺序固定为 canonical -> observed_alias -> query_alias。",
        "observed aliases 只来自 character_profiles_v2.json，不包含 query-only aliases。",
    ]

    if match_type == "canonical":
        notes.append("本次查询直接命中 canonical 名称。")
    elif match_type == "observed_alias":
        notes.append("本次查询通过 observed alias 命中；该名字已在 appearances/raw_name 层真实出现过。")
    elif match_type == "query_alias":
        notes.append("本次查询通过 query alias 命中；它只表示 query-time 支持，不代表已进入 observed aliases。")
    else:
        notes.append("当前查询未在 canonical、observed_alias、query_alias 三层中找到匹配。")

    return notes


def format_appearance_samples(samples: list[dict]) -> list[str]:
    if not samples:
        return ["  （无）"]

    lines: list[str] = []
    has_section_type_tag = False

    for index, sample in enumerate(samples, 1):
        chunk_id = sample.get("chunk_id") or "（未知 chunk）"
        meta = load_chunk_meta(chunk_id)
        section_tag = get_section_type_display_tag(chunk_id)
        chapter_hint = sample.get("chapter_hint") or meta.get("chapter_hint") or "（无章节提示）"

        header = f"  {index}. {chunk_id}"
        if section_tag:
            has_section_type_tag = True
            header += f" {section_tag}"
        header += f" | {chapter_hint}"
        lines.append(header)
        lines.append(f"     raw_name: {sample.get('raw_name') or '（无）'}")
        lines.append(f"     alias_source: {sample.get('alias_source') or '（无）'}")
        lines.append(f"     action: {sample.get('action') or '（无）'}")
        lines.append(f"     emotion: {sample.get('emotion') or '（无）'}")
        if index < len(samples):
            lines.append("")

    if has_section_type_tag:
        lines.append("")
        lines.append("  注：方括号标签来自 chunk.meta.json 的 section_type，仅用于展示提示，不改变证据抽样或事实层含义。")

    return lines


def append_relationship_candidate_lines(lines: list[str], candidates: list[dict]) -> bool:
    lines.append("高频互动对象（候选，前 3 条）:")
    if not candidates:
        lines.append("  （无）")
        return False

    has_section_type_tag = False
    for index, item in enumerate(candidates, 1):
        lines.append(
            f"  {index}. {item.get('related_person') or '（未知人物）'} | 关联片段 {item.get('overlap_chunk_count', 0)}"
        )
        lines.append(f"     互动摘要: {item.get('interaction_sample') or '（无）'}")
        evidence_text, tagged = format_evidence_chunk(item.get("sample_chunk_id"))
        has_section_type_tag = has_section_type_tag or tagged
        lines.append(f"     证据: {evidence_text}")
        if index < len(candidates):
            lines.append("")

    return has_section_type_tag


def append_location_candidate_lines(lines: list[str], candidates: list[dict]) -> bool:
    lines.append("高频共现地点（候选，前 3 条）:")
    if not candidates:
        lines.append("  （无）")
        return False

    has_section_type_tag = False
    for index, item in enumerate(candidates, 1):
        lines.append(
            f"  {index}. {item.get('location_name') or '（未知地点）'} | 共现片段 {item.get('overlap_chunk_count', 0)}"
        )
        evidence_text, tagged = format_evidence_chunk(item.get("sample_chunk_id"))
        has_section_type_tag = has_section_type_tag or tagged
        lines.append(f"     证据: {evidence_text}")
        if index < len(candidates):
            lines.append("")

    return has_section_type_tag


def format_person_result_text(query: str, result: dict | None, show_appearances: int = 0) -> str:
    # 默认文本输出面向人类扫读；轻量联动也只落在这里，结构化消费继续走 --json，尽量不改既有 JSON 合同。
    lines = ["=== 人物查询结果 ===", f"查询词: {query}"]

    if not result:
        lines.append("是否命中: 否")
        lines.append("解析顺序: canonical -> observed_alias -> query_alias")
        lines.append("")
        lines.append("说明:")
        for note in build_person_display_notes(None):
            lines.append(f"  - {note}")
        return "\n".join(lines)

    match_type = result.get("matched_by")
    query_alias_input = query if match_type == "query_alias" else None

    lines.append("是否命中: 是")
    lines.append(f"canonical 名称: {result.get('canonical_name') or '（无）'}")
    lines.append(f"命中方式: {MATCH_TYPE_DISPLAY.get(match_type, match_type or '（无）')}")
    # observed aliases 与 query_alias_input 必须分开显示，避免把 query-time 命中误读成事实层别名。
    lines.append(f"observed aliases: {format_inline_values(result.get('aliases', []))}")
    if query_alias_input is not None:
        lines.append(f"query_alias_input: {query_alias_input}")
    lines.append(f"mention_count: {result.get('mention_count', 0)}")
    lines.append(f"first_chunk: {result.get('first_chunk') or '（无）'}")
    lines.append(f"last_chunk: {result.get('last_chunk') or '（无）'}")

    lines.append("")
    lines.append("说明:")
    for note in build_person_display_notes(match_type):
        lines.append(f"  - {note}")

    lines.append("")
    append_ranked_lines(lines, "高频动作（前 5 条）", result.get("top_actions", []), max_items=5)

    lines.append("")
    append_ranked_lines(lines, "高频情绪（前 5 条）", result.get("top_emotions", []), max_items=5)

    if show_appearances > 0:
        lines.append("")
        lines.append(f"appearance 样本（最多 {show_appearances} 条）:")
        lines.extend(format_appearance_samples(result.get("appearance_samples", [])))

    lines.append("")
    lines.append("轻量联动候选:")
    lines.append("")
    # 输出文案明确写“候选”而不是“事实”，因为首版只展示 relationship/location 聚合提示，
    # 不新增新查询系统，也不把 location 共现或 relationship 摘要误写成高置信事实。
    has_section_type_tag = append_relationship_candidate_lines(
        lines,
        result.get("relationship_candidates", []),
    )
    lines.append("")
    has_section_type_tag = (
        append_location_candidate_lines(lines, result.get("location_candidates", []))
        or has_section_type_tag
    )
    if has_section_type_tag:
        lines.append("")
        lines.append("  注：方括号标签来自 chunk.meta.json 的 section_type，仅用于证据展示提醒，不改变联动逻辑或事实层含义。")

    return "\n".join(lines)


# ── 人物查询（v2） ────────────────────────────────────────────────────────────

def build_observed_alias_lookup(profiles: dict) -> dict[str, str]:
    # 人物查询优先走 v2 profile；observed aliases 只代表 appearances/raw_name 中真实出现过的别名。
    lookup: dict[str, str] = {}
    for canonical_name, profile in profiles.items():
        aliases = profile.get("aliases", [])
        if not isinstance(aliases, list):
            continue
        for alias in aliases:
            if isinstance(alias, str) and alias.strip():
                lookup.setdefault(alias.strip(), canonical_name)
    return lookup


def resolve_person_query(name: str, profiles: dict | None = None, query_aliases: dict | None = None) -> dict | None:
    profiles = profiles if profiles is not None else load_character_profiles_v2()
    query_aliases = query_aliases if query_aliases is not None else load_character_query_aliases_v2()
    observed_alias_lookup = build_observed_alias_lookup(profiles)

    query = name.strip()
    if not query:
        return None

    # 查询解析顺序固定为：canonical -> observed_alias -> query_alias。
    if query in profiles:
        return {
            "matched_name": query,
            "matched_by": "canonical",
            "canonical_name": query,
            "profile": profiles[query],
        }

    if query in observed_alias_lookup:
        canonical_name = observed_alias_lookup[query]
        return {
            "matched_name": query,
            "matched_by": "observed_alias",
            "canonical_name": canonical_name,
            "profile": profiles[canonical_name],
        }

    # query aliases 单独存在，用于查询命中，不代表这些名字已经进入 observed alias 事实层。
    if query in query_aliases:
        canonical_name = query_aliases[query]
        profile = profiles.get(canonical_name)
        if profile:
            return {
                "matched_name": query,
                "matched_by": "query_alias",
                "canonical_name": canonical_name,
                "profile": profile,
            }

    return None


def build_person_result(
    name: str,
    profiles: dict | None = None,
    query_aliases: dict | None = None,
    show_appearances: int = 0,
) -> dict | None:
    resolved = resolve_person_query(name, profiles=profiles, query_aliases=query_aliases)
    if not resolved:
        return None

    profile = resolved["profile"]
    result = {
        "matched_name": resolved["matched_name"],
        "matched_by": resolved["matched_by"],
        "canonical_name": resolved["canonical_name"],
        "aliases": profile.get("aliases", []),
        "mention_count": profile.get("mention_count", 0),
        "first_chunk": profile.get("first_chunk"),
        "last_chunk": profile.get("last_chunk"),
        "top_actions": profile.get("top_actions", []),
        "top_emotions": profile.get("top_emotions", []),
        "relationship_candidates": build_relationship_candidates(resolved["canonical_name"]),
        "location_candidates": build_location_candidates(profile),
    }
    if show_appearances > 0:
        # query 结果默认先给 profile 摘要；只有显式要求时，才附加少量 appearance 样本作为证据层。
        result["appearance_samples"] = load_character_appearance_samples(
            resolved["canonical_name"],
            show_appearances,
        )
    return result


def build_person_json_result(
    name: str,
    profiles: dict | None = None,
    query_aliases: dict | None = None,
    show_appearances: int = 0,
) -> dict:
    # 结构化 JSON 输出面向脚本/其他 AI 消费，保持固定字段并继续区分 observed aliases 与 query aliases。
    # 轻量联动首版只加到默认文本输出，避免过早把候选聚合结果冻结成机器接口合同。
    resolved = resolve_person_query(name, profiles=profiles, query_aliases=query_aliases)
    if not resolved:
        return {
            "query": name,
            "query_type": "person",
            "matched": False,
            "resolved_canonical_name": None,
            "match_type": None,
            "observed_aliases": [],
            "query_alias_input": None,
            "appearance_samples": [],
            "notes": [
                "No person match found in canonical, observed_alias, or query_alias layers.",
            ],
        }

    profile = resolved["profile"]
    match_type = resolved["matched_by"]
    canonical_name = resolved["canonical_name"]
    notes = [
        "Resolution order is canonical -> observed_alias -> query_alias.",
        "observed_aliases come from character_profiles_v2.json and stay separate from query-only aliases.",
    ]
    if match_type == "query_alias":
        notes.append("query_alias_input is query-time only and is not promoted into observed aliases.")

    # appearance_samples 仍只挂在人物命中路径，并且默认可稳定返回空列表。
    appearance_samples = []
    if show_appearances > 0:
        appearance_samples = load_character_appearance_samples(canonical_name, show_appearances)

    return {
        "query": name,
        "query_type": "person",
        "matched": True,
        "resolved_canonical_name": canonical_name,
        "match_type": match_type,
        "observed_aliases": profile.get("aliases", []),
        "query_alias_input": name if match_type == "query_alias" else None,
        "appearance_samples": appearance_samples,
        "notes": notes,
    }


def cmd_person(name: str, show_appearances: int = 0, as_json: bool = False) -> int:
    if as_json:
        result = build_person_json_result(name, show_appearances=show_appearances)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("matched") else 1

    result = build_person_result(name, show_appearances=show_appearances)
    print(format_person_result_text(name, result, show_appearances=show_appearances))
    return 0 if result else 1


# ── 列出所有实体 ──────────────────────────────────────────────────────────────

def cmd_list(field: str) -> None:
    index = load_index(field)
    if not index:
        print(f"索引为空或不存在，请先运行 merge.py（field={field}）")
        return

    label_map = {"characters": "人物", "locations": "地点", "events": "事件"}
    label = label_map.get(field, field)

    print(f"\n=== {label}列表（共 {len(index)} 个，按出现频率排序）===\n")
    for i, (entity, info) in enumerate(index.items(), 1):
        count = info.get("count", 0)
        chunks = info.get("chunks", [])
        chunk_preview = ", ".join(chunks[:5])
        if len(chunks) > 5:
            chunk_preview += f" 等 {len(chunks)} 个"
        print(f"{i:4d}. {entity:<30s} 出现 {count:3d} 次  [{chunk_preview}]")


# ── 全字段搜索 ────────────────────────────────────────────────────────────────

def match_record(rec: dict, keyword: str, field: str | None) -> list[str]:
    """
    在指定 field（或全部字段）中搜索 keyword，返回命中内容列表。
    """
    hits = []
    fields_to_search = [field] if field else SEARCH_FIELDS

    for f in fields_to_search:
        value = rec.get(f)
        if value is None:
            continue
        if isinstance(value, str):
            if keyword in value:
                hits.append(f"{f}: {value}")
        elif isinstance(value, list):
            matched = [v for v in value if isinstance(v, str) and keyword in v]
            if matched:
                hits.append(f"{f}: {', '.join(matched)}")

    return hits


def cmd_search(keyword: str, field: str | None) -> None:
    chunks = load_master_kb()

    results = []
    for rec in chunks:
        hits = match_record(rec, keyword, field)
        if hits:
            results.append((rec, hits))

    if not results:
        scope = f"字段 [{field}]" if field else "全部字段"
        print(f'\n未找到包含 "{keyword}" 的结果（搜索范围：{scope}）')
        return

    scope = f"字段 [{field}]" if field else "全部字段"
    print(f'\n=== 搜索 "{keyword}"（{scope}），共 {len(results)} 条命中 ===\n')
    for rec, hits in results:
        chunk_id = rec.get("chunk_id", "")
        chapter_hint = rec.get("chapter_hint", "")
        char_start = rec.get("char_start", "")
        char_end = rec.get("char_end", "")

        print(f"── {chunk_id} ──")
        print(f"   章节：{chapter_hint}")
        print(f"   位置：字符 {char_start}–{char_end}")
        for hit in hits:
            display = hit if len(hit) <= 200 else hit[:200] + "..."
            print(f"   命中：{display}")
        print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="查询中文长文本知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python Scripts/query.py 江涵
  python Scripts/query.py 贞铃
  python Scripts/query.py --list characters
  python Scripts/query.py --search "荣国府" --field locations
""",
    )
    parser.add_argument(
        "person",
        nargs="?",
        help="人物查询（优先走 v2 profile / alias 层）",
    )
    parser.add_argument(
        "--list",
        choices=["characters", "locations", "events"],
        metavar="FIELD",
        help="列出所有实体：characters / locations / events",
    )
    parser.add_argument(
        "--search",
        metavar="KEYWORD",
        help="搜索关键词",
    )
    parser.add_argument(
        "--field",
        choices=["characters", "events", "locations", "summary", "time_markers"],
        metavar="FIELD",
        help="限定搜索字段（与 --search 配合使用）",
    )
    parser.add_argument(
        "--show-appearances",
        type=int,
        default=0,
        metavar="N",
        help="人物查询命中后，附带前 N 条 appearance 样本",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="人物查询时输出结构化 JSON，便于脚本或其他 AI 直接消费",
    )

    args = parser.parse_args()

    if args.list:
        cmd_list(args.list)
        return
    if args.search:
        cmd_search(args.search, args.field)
        return
    if args.person:
        sys.exit(cmd_person(args.person, show_appearances=args.show_appearances, as_json=args.json))

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
