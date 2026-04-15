"""verify_section_types.py - 验证 section_type 写入结果"""

import glob
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS_DIR = os.path.join(PROJECT_ROOT, "chunks")

tagged = {}
total = 0

for meta_path in sorted(glob.glob(os.path.join(CHUNKS_DIR, "*.meta.json"))):
    total += 1
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    section_type = meta.get("section_type")
    if section_type:
        tagged[section_type] = tagged.get(section_type, 0) + 1

print(f"总 meta.json 数: {total}")
print(f"已标注 section_type: {sum(tagged.values())}")
print(f"未标注（默认 story_scene）: {total - sum(tagged.values())}")
print(f"分布: {json.dumps(tagged, ensure_ascii=False, indent=2)}")

log_path = os.path.join(PROJECT_ROOT, "review", "apply_log.json")
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        log = json.load(f)
    print(f"\napply_log 记录成功: {log.get('success', '?')}")
    if sum(tagged.values()) == log.get("success", -1):
        print("✅ 写入数量与日志一致")
    else:
        print("⚠️ 写入数量与日志不一致，需检查")
