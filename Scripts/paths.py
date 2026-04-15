"""
paths.py — 项目路径常量集中定义（三层资产索引）

本文件是当前活跃核心脚本的优先路径常量入口（query.py、build_generation_context.py 等）。
路径收口仅覆盖已迁移的脚本；legacy / 辅助脚本（extract_canon.py 等）仍各自定义路径，未纳入此文件。
当活跃核心脚本所需路径发生变化时，只需修改此文件即可。

三层资产说明：
  Universal（路径约束型）: prompts/, schema/, universal/, Scripts/
  小说级（Novel-specific）: raw/, chunks/, kb/, state/, logs/, artifacts/
  实验/消费层（Experiment）: outputs/
  项目协调:                 config.json, STATE.json
"""

import os

# ── 项目根目录（以此文件所在的 Scripts/ 目录上一级为基准）────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ──────────────────────────────────────────────────────────────────────────────
# Universal 固定资产（路径约束型：被各脚本硬编码引用，暂不物理迁移到 universal/）
# ──────────────────────────────────────────────────────────────────────────────
PROMPTS_DIR   = os.path.join(BASE_DIR, "prompts")
SCHEMA_DIR    = os.path.join(BASE_DIR, "schema")
UNIVERSAL_DIR = os.path.join(BASE_DIR, "universal")

# 配置文件（被 extract / query / generate 脚本读取）
CONFIG_PATH   = os.path.join(BASE_DIR, "config.json")
STATE_JSON    = os.path.join(BASE_DIR, "STATE.json")

# 提取 prompt 模板
CANON_PROMPT_PATH = os.path.join(PROMPTS_DIR, "extract_canon_prompt.txt")
STYLE_PROMPT_PATH = os.path.join(PROMPTS_DIR, "extract_style_prompt.txt")

# 输出格式 schema
CANON_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "canon_schema.json")
STYLE_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "style_schema.json")
LEGACY_SCHEMA_PATH = os.path.join(BASE_DIR, "schema.json")   # extract.py（legacy）引用

# Scripts 目录自身（被 build_generation_context.py 加入 sys.path）
SCRIPTS_DIR   = os.path.join(BASE_DIR, "Scripts")


# ──────────────────────────────────────────────────────────────────────────────
# 小说级资产（Novel-specific）
# ──────────────────────────────────────────────────────────────────────────────
RAW_DIR       = os.path.join(BASE_DIR, "raw")
CHUNKS_DIR    = os.path.join(BASE_DIR, "chunks")
LOGS_DIR      = os.path.join(BASE_DIR, "logs")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

# KB 目录
KB_DIR             = os.path.join(BASE_DIR, "kb")
KB_MASTER          = os.path.join(KB_DIR, "master_kb.json")
KB_PROFILES_V2     = os.path.join(KB_DIR, "character_profiles_v2.json")
KB_APPEARANCES_V2  = os.path.join(KB_DIR, "character_appearances_v2.jsonl")
KB_QUERY_ALIASES_V2 = os.path.join(KB_DIR, "character_query_aliases_v2.json")
KB_ALIAS_MAP_V2    = os.path.join(KB_DIR, "character_alias_map_v2.json")
KB_RELATIONSHIP    = os.path.join(KB_DIR, "relationship_index.json")
KB_LOCATION        = os.path.join(KB_DIR, "location_index.json")
KB_EVENT           = os.path.join(KB_DIR, "event_index.json")
KB_STYLE_SUMMARY   = os.path.join(KB_DIR, "style_summary.json")
KB_CHARACTERS_DIR  = os.path.join(KB_DIR, "characters")

# KB 遗留文件（v1，只读，不更新）
KB_CHARACTER_INDEX_LEGACY = os.path.join(KB_DIR, "character_index.json")

# 处理状态目录及核心文件
STATE_DIR          = os.path.join(BASE_DIR, "state")
PROCESSED_CANON    = os.path.join(STATE_DIR, "processed_canon.jsonl")
PROCESSED_STYLE    = os.path.join(STATE_DIR, "processed_style.jsonl")
PROGRESS           = os.path.join(STATE_DIR, "progress.json")


# ──────────────────────────────────────────────────────────────────────────────
# 实验/消费层（Experiment / Consumption）
# ──────────────────────────────────────────────────────────────────────────────
OUTPUTS_DIR       = os.path.join(BASE_DIR, "outputs")
OUTPUTS_CANON_DIR = os.path.join(OUTPUTS_DIR, "canon")
OUTPUTS_STYLE_DIR = os.path.join(OUTPUTS_DIR, "style")
OUTPUTS_GEN_DIR   = os.path.join(OUTPUTS_DIR, "generation")
OUTPUTS_ROUND3_DIR = os.path.join(OUTPUTS_DIR, "ab_round3")
