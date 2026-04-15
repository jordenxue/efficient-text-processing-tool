"""
apply_section_types.py
将确认后的 section_type 写入对应 chunk 的 meta.json。
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS_DIR = os.path.join(PROJECT_ROOT, "chunks")
REVIEW_DIR = os.path.join(PROJECT_ROOT, "review")
BACKUP_DIR = os.path.join(REVIEW_DIR, "meta_backups")

VALID_TYPES = {
    "story_scene",
    "front_matter",
    "in_universe_document",
    "setting_exposition",
    "author_meta",
}


def load_entries(input_file):
    entries = []
    skipped = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as ex:
                skipped.append(f"第 {line_num} 行 JSON 解析失败: {ex}")
                continue

            chunk_id = entry.get("chunk_id")
            section_type = entry.get("suggested_type") or entry.get("section_type")

            if not chunk_id or not section_type:
                skipped.append(f"第 {line_num} 行缺少 chunk_id 或 section_type")
                continue

            if section_type not in VALID_TYPES:
                skipped.append(f"第 {line_num} 行 section_type '{section_type}' 不合法")
                continue

            if section_type == "story_scene":
                continue

            entries.append({"chunk_id": chunk_id, "section_type": section_type})

    return entries, skipped


def summarize_types(entries):
    type_counts = {}
    for entry in entries:
        section_type = entry["section_type"]
        type_counts[section_type] = type_counts.get(section_type, 0) + 1
    return type_counts


def ensure_backup(meta_path, backup_path):
    if os.path.exists(backup_path):
        return
    shutil.copy2(meta_path, backup_path)


def main():
    parser = argparse.ArgumentParser(description="写入 section_type 到 meta.json")
    parser.add_argument(
        "--input",
        default=os.path.join(REVIEW_DIR, "confirmed_section_types.jsonl"),
        help="输入文件路径",
    )
    parser.add_argument("--yes", action="store_true", help="跳过交互确认")
    parser.add_argument("--dry-run", action="store_true", help="只输出计划，不实际写入")
    args = parser.parse_args()

    input_file = args.input

    if not os.path.exists(input_file):
        print(f"错误：输入文件不存在: {input_file}")
        sys.exit(1)

    entries, skipped = load_entries(input_file)
    type_counts = summarize_types(entries)

    print(f"输入文件: {input_file}")
    print(f"将写入 {len(entries)} 个 chunk 的 section_type")

    if skipped:
        print(f"跳过 {len(skipped)} 行:")
        for message in skipped:
            print(f"  {message}")

    print("\n按类型分布:")
    for section_type, count in sorted(type_counts.items()):
        print(f"  {section_type}: {count}")

    print("\n前 20 条:")
    for entry in entries[:20]:
        print(f"  {entry['chunk_id']} -> {entry['section_type']}")
    if len(entries) > 20:
        print(f"  ... 还有 {len(entries) - 20} 个")

    if args.dry_run:
        print("\n--dry-run 模式，不执行写入。")
        sys.exit(0)

    if not args.yes:
        print("\n确认写入？(y/n)")
        if input().strip().lower() != "y":
            print("已取消。")
            sys.exit(0)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    success = 0
    errors = []

    for entry in entries:
        chunk_id = entry["chunk_id"]
        section_type = entry["section_type"]
        meta_path = os.path.join(CHUNKS_DIR, f"{chunk_id}.meta.json")

        if not os.path.exists(meta_path):
            errors.append({"chunk_id": chunk_id, "error": "meta.json 不存在"})
            continue

        backup_path = os.path.join(BACKUP_DIR, f"{chunk_id}.meta.json.bak")

        try:
            ensure_backup(meta_path, backup_path)
        except Exception as ex:
            errors.append({"chunk_id": chunk_id, "error": f"备份失败: {ex}"})
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            meta["section_type"] = section_type

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                f.write("\n")

            success += 1
        except Exception as ex:
            errors.append({"chunk_id": chunk_id, "error": str(ex)})

    print("\n写入完成:")
    print(f"  成功: {success}")
    print(f"  失败: {len(errors)}")
    if errors:
        for error in errors:
            print(f"  错误: {error['chunk_id']}: {error['error']}")

    log = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_file,
        "total_entries": len(entries),
        "success": success,
        "errors": errors,
        "skipped": skipped,
        "type_distribution": type_counts,
    }
    log_file = os.path.join(REVIEW_DIR, "apply_log.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  日志: {log_file}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
