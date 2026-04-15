"""
rebuild_character_index.py
--------------------------
从 master_kb.json 重建 character index v2，输出两层：
  - character_appearances_v2.jsonl  （每行一个最小事实单元）
  - character_profiles_v2.json      （按 canonical_name 聚合的 profile）

为什么从 master_kb.json 重建而不是修 character_index.json：
    旧 character_index.json 是 merge.py 的汇总产物，其 actions/emotions 是
    平行数组（不与 chunk_id 对齐），alias 未归一，结构已证实不稳定。
    v2 从原始事实层（master_kb.json 的 canon.characters）重新展开，
    保证每条 appearance 都可溯源到具体 chunk，结构稳定。

数据流（接手者速览）：
    master_kb.json
        └─ chunks[].canon.characters[]      ← 原始事实层
              ↓  alias 归一（三层优先级）
    character_appearances_v2.jsonl          ← Step 1 输出，每行一条出场记录
              ↓  按 canonical_name 聚合
    character_profiles_v2.json             ← Step 4 输出，每个角色一条汇总

Alias 三层文件（优先级从高到低）：
    kb/character_alias_manual_blocklist_v2.json   ← 永不合并的对
    kb/character_alias_manual_confirmed_v2.json   ← 人工确认的 alias
    kb/character_alias_map_v2.json                ← 自动生成的 alias（最低）

下一步扩展点（当前未实现）：
    - 接 LLM 生成 core_traits / summary（在 aggregate_profiles 里加字段即可）
    - 跨 chunk 关系网络（从 master_kb.json 的 canon.relationships 展开）
    - query.py 接入 character_profiles_v2.json 做角色检索
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter


# ---------------------------------------------------------------------------
# Alias 解析
# ---------------------------------------------------------------------------

def load_alias_layers(blocklist_path, confirmed_path, auto_map_path):
    """
    加载 alias 三层约束，返回两个结构：
      blocked_pairs: set of frozenset({a, b}) — 这两个名字永不合并
      alias_to_canonical: dict[raw_name -> canonical_name]

    优先级：manual_blocklist > manual_confirmed > alias_map_auto
    为什么 blocklist 最高：误合并（把不同人物当同一人）比漏合并代价高得多。
    blocklist 一旦命中，后两层均不生效。
    """
    # blocklist: 永不合并的对
    blocked_pairs = set()
    try:
        with open(blocklist_path, encoding="utf-8") as f:
            bl = json.load(f)
        for pair in bl.get("pairs", []):
            blocked_pairs.add(frozenset({pair["a"], pair["b"]}))
    except FileNotFoundError:
        pass

    # confirmed: 人工确认的 alias -> canonical
    confirmed = {}
    try:
        with open(confirmed_path, encoding="utf-8") as f:
            confirmed = json.load(f)
    except FileNotFoundError:
        pass

    # auto map: 自动生成的 alias -> canonical（最低优先级）
    auto_map = {}
    try:
        with open(auto_map_path, encoding="utf-8") as f:
            auto_map = json.load(f)
    except FileNotFoundError:
        pass

    # 合并：confirmed 覆盖 auto，blocklist 最终拦截
    alias_to_canonical = {}
    alias_source = {}  # 记录每个 alias 来源于哪一层

    for alias, canonical in auto_map.items():
        if frozenset({alias, canonical}) not in blocked_pairs:
            alias_to_canonical[alias] = canonical
            alias_source[alias] = "auto"

    for alias, canonical in confirmed.items():
        if frozenset({alias, canonical}) not in blocked_pairs:
            alias_to_canonical[alias] = canonical  # confirmed 覆盖 auto
            alias_source[alias] = "confirmed"

    return blocked_pairs, alias_to_canonical, alias_source


def resolve_canonical(raw_name, alias_to_canonical, alias_source):
    """
    将 raw_name 归一化为 canonical_name。
    如果没有映射，raw_name 本身就是 canonical。
    返回 (canonical_name, alias_source_label)
    """
    if raw_name in alias_to_canonical:
        return alias_to_canonical[raw_name], alias_source.get(raw_name, "auto")
    return raw_name, "identity"


# ---------------------------------------------------------------------------
# Step 1: 从 master_kb.json 展开 appearances
# ---------------------------------------------------------------------------

def expand_appearances(master_kb_path, alias_to_canonical, alias_source, blocked_pairs):
    """
    逐 chunk 遍历 canon.characters，拆出最小事实单元。
    每条 appearance 对应一个角色在一个 chunk 中的一次出场记录。

    为什么用 JSONL 而不是大 JSON 数组：
        appearances 规模可达数万条。JSONL 支持流式读写，
        便于后续脚本逐行处理而无需全量加载到内存。
    """
    with open(master_kb_path, encoding="utf-8") as f:
        master = json.load(f)

    chunks = master.get("chunks", [])

    appearances = []
    stats = {"blocklist_blocked": 0, "confirmed": 0, "auto": 0, "identity": 0}

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        chapter_hint = chunk.get("chapter_hint", None)
        char_start = chunk.get("char_start", None)
        char_end = chunk.get("char_end", None)
        canon = chunk.get("canon") or {}
        characters = canon.get("characters") or []

        for char_entry in characters:
            raw_name = (char_entry.get("name") or "").strip()
            if not raw_name:
                continue

            action = char_entry.get("action") or None
            emotion = char_entry.get("emotion") or None

            canonical_name, src = resolve_canonical(raw_name, alias_to_canonical, alias_source)
            stats[src] = stats.get(src, 0) + 1

            appearances.append({
                "canonical_name": canonical_name,
                "raw_name": raw_name,
                "chunk_id": chunk_id,
                "chapter_hint": chapter_hint,
                "char_start": char_start,
                "char_end": char_end,
                "action": action,
                "emotion": emotion,
                "alias_source": src,
            })

    return appearances, chunks, stats


# ---------------------------------------------------------------------------
# Step 4: 聚合 profiles
# ---------------------------------------------------------------------------

def aggregate_profiles(appearances, top_n=20):
    """
    按 canonical_name 聚合所有 appearances，生成 profile。
    top_actions / top_emotions 做频次排序，保留前 top_n 条。
    不接 LLM，先把结构跑通。
    """
    groups = defaultdict(list)
    for app in appearances:
        groups[app["canonical_name"]].append(app)

    profiles = {}
    for canonical_name, apps in groups.items():
        chunk_ids = [a["chunk_id"] for a in apps]
        # 保留出现过该角色的唯一 chunk（按原始顺序）
        seen = set()
        unique_chunks = []
        for c in chunk_ids:
            if c not in seen:
                seen.add(c)
                unique_chunks.append(c)

        # 收集 raw_name 别名集合（排除与 canonical 相同的）
        aliases = sorted({a["raw_name"] for a in apps if a["raw_name"] != canonical_name})

        # 统计 action / emotion 频次
        actions = [a["action"] for a in apps if a["action"]]
        emotions = [a["emotion"] for a in apps if a["emotion"]]

        # emotion 字段可能是逗号分隔的复合词（如"困惑、不知所措"），拆开统计
        emotion_tokens = []
        for e in emotions:
            for token in e.replace("，", "、").replace(",", "、").split("、"):
                t = token.strip()
                if t:
                    emotion_tokens.append(t)

        top_actions = [item for item, _ in Counter(actions).most_common(top_n)]
        top_emotions = [item for item, _ in Counter(emotion_tokens).most_common(top_n)]

        profiles[canonical_name] = {
            "canonical_name": canonical_name,
            "aliases": aliases,
            "mention_count": len(apps),
            "first_chunk": unique_chunks[0] if unique_chunks else None,
            "last_chunk": unique_chunks[-1] if unique_chunks else None,
            "chunk_ids": unique_chunks,
            "top_actions": top_actions,
            "top_emotions": top_emotions,
        }

    return profiles


# ---------------------------------------------------------------------------
# 写出
# ---------------------------------------------------------------------------

def write_appearances_jsonl(appearances, path):
    with open(path, "w", encoding="utf-8") as f:
        for app in appearances:
            f.write(json.dumps(app, ensure_ascii=False) + "\n")


def write_profiles_json(profiles, path):
    # 按 mention_count 降序输出，便于人工浏览
    sorted_profiles = dict(
        sorted(profiles.items(), key=lambda x: x[1]["mention_count"], reverse=True)
    )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted_profiles, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 编码自检
# ---------------------------------------------------------------------------

def encoding_check(appearances_path, profiles_path):
    ok = True
    try:
        with open(appearances_path, encoding="utf-8") as f:
            first_line = f.readline()
        obj = json.loads(first_line)
        if obj.get("canonical_name") and all(ord(c) < 128 for c in obj["canonical_name"]):
            ok = False
    except Exception:
        ok = False

    try:
        with open(profiles_path, encoding="utf-8") as f:
            profiles = json.load(f)
        first_key = list(profiles.keys())[0]
        if all(ord(c) < 128 for c in first_key):
            ok = False
    except Exception:
        ok = False

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="从 master_kb.json 重建 character index v2")
    parser.add_argument("--master-kb", default="kb/master_kb.json")
    parser.add_argument("--manual-confirmed", default="kb/character_alias_manual_confirmed_v2.json")
    parser.add_argument("--manual-blocklist", default="kb/character_alias_manual_blocklist_v2.json")
    parser.add_argument("--auto-alias-map", default="kb/character_alias_map_v2.json")
    parser.add_argument("--appearances-out", default="kb/character_appearances_v2.jsonl")
    parser.add_argument("--profiles-out", default="kb/character_profiles_v2.json")
    args = parser.parse_args()

    master_kb_path = Path(args.master_kb)
    appearances_path = Path(args.appearances_out)
    profiles_path = Path(args.profiles_out)

    print(f"读取 alias 三层约束...")
    blocked_pairs, alias_to_canonical, alias_source = load_alias_layers(
        Path(args.manual_blocklist),
        Path(args.manual_confirmed),
        Path(args.auto_alias_map),
    )
    print(f"  blocklist 对数: {len(blocked_pairs)}")
    print(f"  confirmed alias 数: {sum(1 for s in alias_source.values() if s == 'confirmed')}")
    print(f"  auto alias 数: {sum(1 for s in alias_source.values() if s == 'auto')}")

    print(f"\n读取 {master_kb_path}...")
    appearances, chunks, stats = expand_appearances(
        master_kb_path, alias_to_canonical, alias_source, blocked_pairs
    )

    print(f"\n聚合 profiles...")
    profiles = aggregate_profiles(appearances)

    print(f"\n写出文件...")
    write_appearances_jsonl(appearances, appearances_path)
    write_profiles_json(profiles, profiles_path)

    enc_ok = encoding_check(appearances_path, profiles_path)

    print()
    print("=" * 55)
    print(f"读取 chunk 数:          {len(chunks)}")
    print(f"生成 appearance 数:     {len(appearances)}")
    print(f"生成 canonical profile: {len(profiles)}")
    print()
    print(f"alias 来源统计:")
    print(f"  identity（无映射）:   {stats.get('identity', 0)}")
    print(f"  confirmed（人工）:    {stats.get('confirmed', 0)}")
    print(f"  auto（自动）:         {stats.get('auto', 0)}")
    print()
    print(f"输出文件:")
    print(f"  appearances -> {appearances_path}")
    print(f"  profiles    -> {profiles_path}")
    print()
    print(f"编码自检: {'PASS' if enc_ok else 'WARN - 请检查输出文件编码'}")
    print()

    # 打印 mention_count 前10 的 profile，快速验证
    top10 = sorted(profiles.items(), key=lambda x: x[1]["mention_count"], reverse=True)[:10]
    print("mention_count 前10角色:")
    for name, p in top10:
        alias_str = f"  (aliases: {', '.join(p['aliases'])})" if p["aliases"] else ""
        print(f"  {name:12s}  {p['mention_count']:5d} 次{alias_str}")
    print("=" * 55)
    print("不影响主流程：只读 master_kb.json 和 alias 文件，只写新 v2 文件，不修改任何现有 kb 文件。")


if __name__ == "__main__":
    main()
