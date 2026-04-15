"""
build_character_query_aliases.py
--------------------------------
构建 query-time alias 层。

为什么要单独做 query aliases：
- profiles.aliases 更接近 observed aliases，只收录在 appearances/raw_name 中真实出现过的别名
- 某些昵称只用于查询命中，并不回写到事实层 profile.aliases
- blocklist 优先级最高，防止把已确认不应归一的名字重新并进查询映射
"""

import argparse
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MANUAL_CONFIRMED = BASE_DIR / "kb" / "character_alias_manual_confirmed_v2.json"
DEFAULT_MANUAL_BLOCKLIST = BASE_DIR / "kb" / "character_alias_manual_blocklist_v2.json"
DEFAULT_AUTO_ALIAS_MAP = BASE_DIR / "kb" / "character_alias_map_v2.json"
DEFAULT_OUT = BASE_DIR / "kb" / "character_query_aliases_v2.json"

QUERY_ONLY_NICKNAMES = {
    "猫猫涵": "江涵",
    "涵猫猫": "江涵",
    "涵宝": "江涵",
    "憨包": "江涵",
}


def load_mapping(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"映射文件不是 object: {path}")
    return {
        str(alias).strip(): str(canonical).strip()
        for alias, canonical in data.items()
        if str(alias).strip() and str(canonical).strip()
    }


def load_blocklist_pairs(path: Path) -> set[tuple[str, str]]:
    if not path.is_file():
        return set()

    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = data.get("pairs", [])
    if not isinstance(pairs, list):
        raise ValueError(f"blocklist pairs 不是 list: {path}")

    blocked: set[tuple[str, str]] = set()
    for item in pairs:
        if not isinstance(item, dict):
            continue
        a = str(item.get("a", "")).strip()
        b = str(item.get("b", "")).strip()
        if not a or not b:
            continue
        blocked.add(tuple(sorted((a, b))))
    return blocked


def is_blocked(alias: str, canonical: str, blocked_pairs: set[tuple[str, str]]) -> bool:
    return tuple(sorted((alias, canonical))) in blocked_pairs


def merge_aliases(
    blocked_pairs: set[tuple[str, str]],
    manual_confirmed: dict[str, str],
    auto_alias_map: dict[str, str],
    query_only_nicknames: dict[str, str],
) -> dict[str, str]:
    final_map: dict[str, str] = {}

    for alias, canonical in manual_confirmed.items():
        if is_blocked(alias, canonical, blocked_pairs):
            continue
        final_map[alias] = canonical

    for alias, canonical in auto_alias_map.items():
        if is_blocked(alias, canonical, blocked_pairs):
            continue
        final_map.setdefault(alias, canonical)

    for alias, canonical in query_only_nicknames.items():
        if is_blocked(alias, canonical, blocked_pairs):
            continue
        final_map[alias] = canonical

    return dict(sorted(final_map.items(), key=lambda x: x[0]))


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 character query aliases v2")
    parser.add_argument("--manual-confirmed", default=str(DEFAULT_MANUAL_CONFIRMED))
    parser.add_argument("--manual-blocklist", default=str(DEFAULT_MANUAL_BLOCKLIST))
    parser.add_argument("--auto-alias-map", default=str(DEFAULT_AUTO_ALIAS_MAP))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    manual_confirmed_path = Path(args.manual_confirmed)
    manual_blocklist_path = Path(args.manual_blocklist)
    auto_alias_map_path = Path(args.auto_alias_map)
    out_path = Path(args.out)

    blocked_pairs = load_blocklist_pairs(manual_blocklist_path)
    manual_confirmed = load_mapping(manual_confirmed_path)
    auto_alias_map = load_mapping(auto_alias_map_path)

    final_map = merge_aliases(
        blocked_pairs=blocked_pairs,
        manual_confirmed=manual_confirmed,
        auto_alias_map=auto_alias_map,
        query_only_nicknames=QUERY_ONLY_NICKNAMES,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(final_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"blocklist_pair_count = {len(blocked_pairs)}")
    print(f"manual_confirmed_count = {len(manual_confirmed)}")
    print(f"auto_alias_count = {len(auto_alias_map)}")
    print(f"query_only_nickname_count = {len(QUERY_ONLY_NICKNAMES)}")
    print(f"final_query_alias_count = {len(final_map)}")
    print(f"output = {out_path}")


if __name__ == "__main__":
    main()
