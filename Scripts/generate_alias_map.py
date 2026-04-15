"""
generate_alias_map.py
---------------------
为 character_index v2 重建准备 alias 层。

为什么先做 alias 层：
    character_index.json 中存在大量未归一的别名（如"贞铃"和"江贞铃"被当作
    独立角色分别统计），直接用于重建 profile 会导致同一人物数据碎片化。
    必须先确定哪些名字是同一人物的别称，再合并统计，才能得到稳定的 v2 profile。

只读现有 kb，不改主流程任何文件。
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# 自动接受规则（保守）
# 为什么保守：alias 层一旦落表就会在 v2 重建中合并数据。误合并比漏合并代价更高。
# ---------------------------------------------------------------------------
AUTO_ACCEPT_RULES = {
    # alias 必须是 canonical 的真子串（不等于 canonical）
    "substring": True,
    # alias 长度 >= 2（排除单字名，单字名容易误匹配）
    "min_alias_len": 2,
    # canonical 长度必须 > alias 长度（canonical 必须更长）
    "canonical_longer": True,
    # canonical 出现频率必须明显高于 alias：alias_count < canonical_count * 0.4
    "freq_ratio_threshold": 0.4,
    # canonical 必须出现足够多次，避免低频噪声角色主导合并
    "min_canonical_count": 10,
    # canonical 长度 >= 3（两字名作为 canonical 时更容易是误匹配）
    "min_canonical_len": 3,
}


def load_character_index(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_count(entry) -> int:
    """兼容 count 字段为整数或缺失的情况。"""
    if isinstance(entry, dict):
        return entry.get("count", 0)
    return 0


def compute_candidates(char_index: dict) -> list:
    """
    对所有名字两两比较，找出子串关系候选。

    只做保守规则，不做 NLP / 编辑距离等复杂匹配：
    - A 是 B 的真子串
    - len(A) >= 2
    - count(A) < count(B) * 0.5   ← 初筛阈值，比自动接受更宽松，保证候选完整
    """
    names = list(char_index.keys())
    counts = {n: get_count(char_index[n]) for n in names}

    # 按长度降序，方便后续只往"更短 → 更长"方向检查
    names_by_len = sorted(names, key=lambda x: len(x), reverse=True)

    candidates = []
    seen_pairs = set()

    for i, longer in enumerate(names_by_len):
        for shorter in names_by_len[i + 1 :]:
            if len(shorter) < 2:
                continue
            if shorter not in longer:
                continue
            if shorter == longer:
                continue

            pair_key = (shorter, longer)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            alias_count = counts[shorter]
            canonical_count = counts[longer]

            # 候选初筛：alias 频率 < canonical 频率的 50%，或 canonical 明显更常见
            if canonical_count == 0:
                continue
            ratio = alias_count / canonical_count if canonical_count > 0 else 999

            if ratio >= 0.5:
                # 两边频率接近，不作为候选（以下情况只进 review，不进 map）
                # 这些候选最多进 review，不自动接受
                rule = "freq_close_skip"
                confidence = "low"
                auto_accept = False
                reason = f"频率接近（ratio={ratio:.2f}），可能是独立角色"
            else:
                rule, confidence, auto_accept, reason = evaluate_candidate(
                    shorter, longer, alias_count, canonical_count, ratio
                )

            candidates.append(
                {
                    "alias": shorter,
                    "canonical_candidate": longer,
                    "alias_count": alias_count,
                    "canonical_count": canonical_count,
                    "rule": rule,
                    "confidence": confidence,
                    "auto_accept": auto_accept,
                    "reason": reason,
                }
            )

    # 按置信度排序：high > medium > low
    order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda x: (order.get(x["confidence"], 3), -x["canonical_count"]))
    return candidates


def evaluate_candidate(
    alias: str,
    canonical: str,
    alias_count: int,
    canonical_count: int,
    ratio: float,
) -> tuple:
    """
    对已通过初筛的候选（ratio < 0.5）进一步分层。

    自动接受标准（必须同时满足）：
    1. alias 长度 >= AUTO_ACCEPT_RULES["min_alias_len"]  （排除单字）
    2. canonical 长度 >= AUTO_ACCEPT_RULES["min_canonical_len"]（排除两字 canonical）
    3. canonical_count >= AUTO_ACCEPT_RULES["min_canonical_count"]（canonical 够稳定）
    4. ratio < AUTO_ACCEPT_RULES["freq_ratio_threshold"]（频率差足够大）

    不满足则降为 medium 或 low，只进 candidates，不进 alias_map。
    """
    rules = AUTO_ACCEPT_RULES

    fails = []

    if len(alias) < rules["min_alias_len"]:
        fails.append(f"alias太短({len(alias)}字)")
    if len(canonical) < rules["min_canonical_len"]:
        fails.append(f"canonical太短({len(canonical)}字)")
    if canonical_count < rules["min_canonical_count"]:
        fails.append(f"canonical低频({canonical_count}次)")
    if ratio >= rules["freq_ratio_threshold"]:
        fails.append(f"频率差不足(ratio={ratio:.2f})")

    if not fails:
        return (
            "substring_auto",
            "high",
            True,
            f"子串简称，频率差显著(ratio={ratio:.2f})，canonical出现{canonical_count}次",
        )

    # 有部分失败，降为 medium（仍值得人工审查）
    if len(fails) <= 1 and canonical_count >= 5:
        return (
            "substring_review",
            "medium",
            False,
            f"需人工确认：{'; '.join(fails)}",
        )

    # 多项失败，low，进 review 但排在末尾
    return (
        "substring_weak",
        "low",
        False,
        f"弱候选，不建议合并：{'; '.join(fails)}",
    )


def build_alias_map(candidates: list) -> dict:
    """
    只从 auto_accept=True 的候选构建 alias_map。
    如果同一 alias 有多个 canonical 候选（极罕见），取 canonical_count 最大的。
    """
    best: dict[str, dict] = {}
    for c in candidates:
        if not c["auto_accept"]:
            continue
        alias = c["alias"]
        if alias not in best or c["canonical_count"] > best[alias]["canonical_count"]:
            best[alias] = c

    return {alias: entry["canonical_candidate"] for alias, entry in best.items()}


def build_review_md(candidates: list, alias_map: dict) -> str:
    accepted = [c for c in candidates if c["auto_accept"]]
    review = [c for c in candidates if not c["auto_accept"] and c["confidence"] == "medium"]
    low = [c for c in candidates if not c["auto_accept"] and c["confidence"] == "low"]

    lines = [
        "# Character Alias Review v2",
        "",
        f"总候选数: {len(candidates)}  |  自动接受: {len(accepted)}  |  需人工审查: {len(review)}  |  低置信丢弃: {len(low)}",
        "",
        "---",
        "",
        "## Auto Accepted（已写入 alias_map）",
        "",
        "| alias | canonical | alias次数 | canonical次数 | ratio | reason |",
        "| ----- | --------- | --------- | ------------- | ----- | ------ |",
    ]
    for c in accepted:
        ratio = c["alias_count"] / c["canonical_count"] if c["canonical_count"] else 0
        lines.append(
            f"| {c['alias']} | {c['canonical_candidate']} | {c['alias_count']} "
            f"| {c['canonical_count']} | {ratio:.2f} | {c['reason']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Needs Manual Review（medium confidence，未写入 alias_map）",
        "",
        "| alias | canonical | alias次数 | canonical次数 | ratio | reason |",
        "| ----- | --------- | --------- | ------------- | ----- | ------ |",
    ]
    for c in review:
        ratio = c["alias_count"] / c["canonical_count"] if c["canonical_count"] else 0
        lines.append(
            f"| {c['alias']} | {c['canonical_candidate']} | {c['alias_count']} "
            f"| {c['canonical_count']} | {ratio:.2f} | {c['reason']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Low Confidence（不建议合并）",
        "",
        "| alias | canonical | alias次数 | canonical次数 | reason |",
        "| ----- | --------- | --------- | ------------- | ------ |",
    ]
    for c in low:
        lines.append(
            f"| {c['alias']} | {c['canonical_candidate']} | {c['alias_count']} "
            f"| {c['canonical_count']} | {c['reason']} |"
        )

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="生成 character alias 候选与初版映射")
    parser.add_argument("--input", default="kb/character_index.json")
    parser.add_argument("--candidates-out", default="kb/character_alias_candidates_v2.json")
    parser.add_argument("--map-out", default="kb/character_alias_map_v2.json")
    parser.add_argument("--review-out", default="kb/character_alias_review_v2.md")
    args = parser.parse_args()

    input_path = Path(args.input)
    candidates_path = Path(args.candidates_out)
    map_path = Path(args.map_out)
    review_path = Path(args.review_out)

    print(f"读取: {input_path}")
    char_index = load_character_index(input_path)
    total_chars = len(char_index)
    print(f"  总角色数: {total_chars}")

    print("计算候选...")
    candidates = compute_candidates(char_index)
    total_candidates = len(candidates)
    accepted = [c for c in candidates if c["auto_accept"]]
    total_accepted = len(accepted)

    alias_map = build_alias_map(candidates)
    review_md = build_review_md(candidates, alias_map)

    # 写出所有文件，统一使用 utf-8，ensure_ascii=False 保留中文
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(alias_map, f, ensure_ascii=False, indent=2)

    with open(review_path, "w", encoding="utf-8") as f:
        f.write(review_md)

    # ---------------------------------------------------------------------------
    # 输出文件自检：读回并验证中文键名未损坏
    # ---------------------------------------------------------------------------
    with open(candidates_path, encoding="utf-8") as f:
        check_candidates = json.load(f)
    with open(map_path, encoding="utf-8") as f:
        check_map = json.load(f)

    # 验证：第一条候选的 alias 字段是否仍是中文（非 ????）
    enc_ok = True
    if check_candidates:
        sample_alias = check_candidates[0]["alias"]
        if all(ord(c) < 128 for c in sample_alias):
            enc_ok = False
    if check_map:
        sample_key = list(check_map.keys())[0]
        if all(ord(c) < 128 for c in sample_key):
            enc_ok = False

    print()
    print("=" * 50)
    print(f"总角色数:       {total_chars}")
    print(f"候选数:         {total_candidates}")
    print(f"自动接受数:     {total_accepted}")
    print()
    print(f"输出文件:")
    print(f"  candidates -> {candidates_path}")
    print(f"  alias_map  -> {map_path}")
    print(f"  review     -> {review_path}")
    print()
    print(f"编码自检: {'PASS - 中文键名正常' if enc_ok else 'WARN - 请检查输出文件编码'}")
    print()
    print("Auto accepted 示例（前10条）:")
    for c in accepted[:10]:
        ratio = c["alias_count"] / c["canonical_count"] if c["canonical_count"] else 0
        print(f"  {c['alias']:8s} -> {c['canonical_candidate']:12s}  "
              f"({c['alias_count']} / {c['canonical_count']}, ratio={ratio:.2f})")
    print("=" * 50)
    print("不影响主流程：本脚本只读 character_index.json，只写新文件，不修改任何现有 kb 文件。")


if __name__ == "__main__":
    main()
