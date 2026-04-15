"""
extract_canon.py — Canon 管道：抽取叙事结构（人物行为/事件因果/关系互动）
用法：
  python Scripts/extract_canon.py              # 处理全部未完成的 chunk
  python Scripts/extract_canon.py --limit 10   # 只处理前 10 个未完成的 chunk

V1 structural_chunk 门控：
  MIN_CHARS = 200  且  （单/双行 且 含章节标题模式）→ 跳过 API，记录为 structural_chunk
"""

import os
import sys
import json
import time
import re
import uuid
import logging
import datetime
import argparse

import requests
import jsonschema

# ── 路径基准 ─────────────────────────────────────────────────────────────────
# 注：此脚本已完成使命（canon full run 已完毕，不重跑），路径保持原样不迁移到 paths.py。
# 若未来需要再次运行，可将下方常量替换为 paths.py 中的对应项（CONFIG_PATH、CANON_SCHEMA_PATH 等）。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH  = os.path.join(BASE_DIR, "config.json")
SCHEMA_PATH  = os.path.join(BASE_DIR, "schema", "canon_schema.json")
PROMPT_PATH  = os.path.join(BASE_DIR, "prompts", "extract_canon_prompt.txt")
CHUNKS_DIR   = os.path.join(BASE_DIR, "chunks")
OUTPUTS_DIR  = os.path.join(BASE_DIR, "outputs", "canon")
LOGS_DIR     = os.path.join(BASE_DIR, "logs")
STATE_DIR    = os.path.join(BASE_DIR, "state")

STATE_FILE            = os.path.join(STATE_DIR, "processed_canon.jsonl")
BAD_CHUNKS_FILE       = os.path.join(LOGS_DIR,  "bad_chunks_canon.jsonl")
STRUCTURAL_LOG_FILE   = os.path.join(LOGS_DIR,  "structural_chunks_canon.jsonl")
RUN_SUMMARY_FILE      = os.path.join(LOGS_DIR,  "run_summary_canon.json")

# ── V1 structural_chunk 门控参数 ──────────────────────────────────────────────
MIN_CHARS = 200   # 低于此值直接视为结构性 chunk

_TITLE_RE = re.compile(
    r"^("
    r"第[零一二三四五六七八九十百千万\d]+[章节回卷篇部幕]"
    r"|Chapter\s*\d+"
    r"|卷[零一二三四五六七八九十百千万\d]+"
    r"|第[零一二三四五六七八九十百千万\d]+话"
    r"|楔子|序章|序言|前言|引子|番外|尾声|终章|后记|后序"
    r"|上篇|下篇|上卷|下卷|中卷"
    r")",
    re.MULTILINE,
)

for d in (OUTPUTS_DIR, LOGS_DIR, STATE_DIR):
    os.makedirs(d, exist_ok=True)

# ── 日志 ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "extract_canon.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── 配置 & 资源 ───────────────────────────────────────────────────────────────
with open(CONFIG_PATH, encoding="utf-8") as f:
    CONFIG = json.load(f)

with open(SCHEMA_PATH, encoding="utf-8") as f:
    SCHEMA = json.load(f)

with open(PROMPT_PATH, encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

BASE_URL    = CONFIG["base_url"].rstrip("/")
MODEL       = CONFIG["model"]
RETRY_COUNT = CONFIG["retry_count"]

PROMPT_VERSION = "canon_v2"
SCHEMA_VERSION = "canon_v1"


# ── 断点续跑状态 ──────────────────────────────────────────────────────────────

def load_processed() -> set:
    """返回已处理完毕的 chunk_id 集合（含 success 与 structural_chunk）。"""
    done = set()
    if not os.path.isfile(STATE_FILE):
        return done
    with open(STATE_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("status") in ("success", "structural_chunk"):
                    done.add(rec["chunk_id"])
            except json.JSONDecodeError:
                pass
    return done


def record_state(chunk_id: str, status: str, extra: dict | None = None) -> None:
    rec = {"chunk_id": chunk_id, "status": status,
           "ts": datetime.datetime.now().isoformat()}
    if extra:
        rec.update(extra)
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def record_bad(chunk_id: str, reason: str, raw_response: str) -> None:
    rec = {
        "chunk_id": chunk_id,
        "reason": reason,
        "raw_response": raw_response[:2000],
        "ts": datetime.datetime.now().isoformat(),
    }
    with open(BAD_CHUNKS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def record_structural(chunk_id: str, reason: str, char_count: int) -> None:
    rec = {
        "chunk_id": chunk_id,
        "reason": reason,
        "char_count": char_count,
        "ts": datetime.datetime.now().isoformat(),
    }
    with open(STRUCTURAL_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ── V1 structural_chunk 判定 ──────────────────────────────────────────────────

def is_structural_chunk(chunk_text: str, meta: dict) -> tuple[bool, str]:
    """
    V1 两级规则（便宜稳定，不上语义分类器）：
      Rule-1: len < MIN_CHARS
      Rule-2: 文本为单行或双行，且首行匹配章节标题正则
    返回 (is_structural: bool, reason: str)
    """
    text = chunk_text.strip()
    length = len(text)

    # Rule-1：字符数门控
    if length < MIN_CHARS:
        return True, f"too_short ({length} chars < {MIN_CHARS})"

    # Rule-2：单/双行 + 标题模式
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) <= 2 and lines and _TITLE_RE.match(lines[0]):
        return True, f"title_pattern ({len(lines)} lines, first='{lines[0][:30]}')"

    return False, ""


# ── JSON 预清洗 ───────────────────────────────────────────────────────────────

def clean_json_text(text: str) -> str:
    """
    1. 去除 markdown 代码块标记
    2. 截取第一个完整 JSON 对象 { ... }
    3. 修复末尾多余逗号（, } 或 , ]）
    """
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip()

    brace_start = text.find("{")
    if brace_start == -1:
        return text
    depth = 0
    brace_end = -1
    for i, ch in enumerate(text[brace_start:], start=brace_start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                brace_end = i
                break
    if brace_end != -1:
        text = text[brace_start: brace_end + 1]

    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


# ── API 调用 ──────────────────────────────────────────────────────────────────

def call_api(chunk_id: str, chunk_text: str) -> str:
    """调用 OpenAI 兼容 API，返回原始文本响应。"""
    user_message = f"chunk_id: {chunk_id}\n\n{chunk_text}"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
    }
    url = f"{BASE_URL}/chat/completions"
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ── 核心处理 ──────────────────────────────────────────────────────────────────

def process_chunk(chunk_id: str, chunk_text: str, meta: dict) -> bool:
    """尝试 1 + retry_count 次。成功返回 True，失败返回 False。"""
    last_raw = ""
    for attempt in range(1 + RETRY_COUNT):
        try:
            logger.info("[%s] 第 %d 次尝试...", chunk_id, attempt + 1)
            raw = call_api(chunk_id, chunk_text)
            last_raw = raw
            cleaned = clean_json_text(raw)
            parsed = json.loads(cleaned)
            parsed["chunk_id"] = chunk_id  # 防止模型填错
            jsonschema.validate(instance=parsed, schema=SCHEMA)

            output = {**meta, **parsed}
            out_path = os.path.join(OUTPUTS_DIR, f"{chunk_id}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            record_state(chunk_id, "success")
            logger.info("[%s] 成功", chunk_id)
            return True

        except requests.RequestException as e:
            logger.warning("[%s] 网络错误：%s", chunk_id, e)
            if attempt < RETRY_COUNT:
                time.sleep(2)
        except json.JSONDecodeError as e:
            logger.warning("[%s] JSON 解析失败：%s", chunk_id, e)
        except jsonschema.ValidationError as e:
            logger.warning("[%s] Schema 校验失败：%s", chunk_id, e.message)
        except Exception as e:
            logger.warning("[%s] 未知错误：%s", chunk_id, e)
            if attempt < RETRY_COUNT:
                time.sleep(1)

    record_state(chunk_id, "failed")
    record_bad(chunk_id, "max_retries_exceeded", last_raw)
    logger.error("[%s] 已达最大重试次数，跳过", chunk_id)
    return False


def collect_chunks() -> list[tuple[str, str, dict]]:
    """扫描 chunks/ 目录，返回 [(chunk_id, text, meta), ...]，按 chunk_id 排序。"""
    items = []
    for fname in os.listdir(CHUNKS_DIR):
        if not fname.endswith(".txt"):
            continue
        chunk_id  = fname[:-4]
        txt_path  = os.path.join(CHUNKS_DIR, fname)
        meta_path = os.path.join(CHUNKS_DIR, f"{chunk_id}.meta.json")

        with open(txt_path, encoding="utf-8") as f:
            chunk_text = f.read().strip()

        meta = {}
        if os.path.isfile(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)

        items.append((chunk_id, chunk_text, meta))

    items.sort(key=lambda x: x[0])
    return items


# ── 主函数 ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Canon 管道：抽取叙事结构信息")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="处理未完成列表中（经 offset 后）的前 N 个 chunk，不指定则处理全部",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        metavar="N",
        help="从未完成 chunk 列表跳过前 N 个，再处理后面的 --limit M 个（默认 0）",
    )
    args = parser.parse_args()
    limit  = args.limit
    offset = args.offset

    run_id   = str(uuid.uuid4())[:8]
    ts_start = datetime.datetime.now().isoformat()
    log_suffix = (f"  limit={limit}" if limit is not None else "") + \
                 (f"  offset={offset}" if offset else "")
    logger.info("=== Canon 管道  run_id=%s%s ===", run_id, log_suffix)

    done_set   = load_processed()
    all_chunks = collect_chunks()
    total      = len(all_chunks)
    done_count = sum(1 for cid, _, _ in all_chunks if cid in done_set)
    logger.info("已完成（断点续跑）：%d  /  扫描到：%d", done_count, total)

    # ── 构建待处理列表，应用 offset ──────────────────────────────────────────
    pending = [
        (cid, txt, meta)
        for cid, txt, meta in all_chunks
        if cid not in done_set and txt.strip()
    ]
    if offset:
        actual_skip = min(offset, len(pending))
        logger.info("--offset %d：跳过待处理列表前 %d 个", offset, actual_skip)
        pending = pending[offset:]

    success_count      = 0
    failed_count       = 0
    structural_count   = 0
    processed_this_run = 0

    for chunk_id, chunk_text, meta in pending:
        if limit is not None and processed_this_run >= limit:
            logger.info("已达 --limit %d，停止处理", limit)
            break

        # ── V1 门控 ──────────────────────────────────────────────────────────
        structural, reason = is_structural_chunk(chunk_text, meta)
        if structural:
            logger.info("[%s] structural_chunk，跳过 API（%s）", chunk_id, reason)
            record_state(chunk_id, "structural_chunk")
            record_structural(chunk_id, reason, len(chunk_text.strip()))
            structural_count   += 1
            processed_this_run += 1
            continue

        ok = process_chunk(chunk_id, chunk_text, meta)
        processed_this_run += 1
        if ok:
            success_count += 1
        else:
            failed_count += 1

    summary = {
        "run_id":             run_id,
        "pipeline":           "canon",
        "prompt_version":     PROMPT_VERSION,
        "schema_version":     SCHEMA_VERSION,
        "timestamp":          ts_start,
        "total":              total,
        "done_before_run":    done_count,
        "offset":             offset,
        "success":            success_count,
        "failed":             failed_count,
        "structural":         structural_count,
        "processed_this_run": processed_this_run,
    }
    with open(RUN_SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info("运行结束：total=%d  done_before=%d  processed=%d  success=%d  failed=%d  structural=%d",
                total, done_count, processed_this_run, success_count, failed_count, structural_count)
    print(f"\n完成！本次处理 {processed_this_run}，成功 {success_count}，失败 {failed_count}，structural {structural_count}")
    print(f"运行摘要：{RUN_SUMMARY_FILE}")


if __name__ == "__main__":
    main()
