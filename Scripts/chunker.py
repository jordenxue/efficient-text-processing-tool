"""
chunker.py — 将 raw/ 下的 txt 文件切分为 chunks/
用法：
  python Scripts/chunker.py raw/某书.txt
  python Scripts/chunker.py raw/某书.txt --limit-chars 50000
  python Scripts/chunker.py raw/某书.txt --limit-lines 1000
"""

import re
import os
import sys
import json
import logging
import argparse
import datetime

# ── 路径基准 ─────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CHUNKS_DIR  = os.path.join(BASE_DIR, "chunks")
LOGS_DIR    = os.path.join(BASE_DIR, "logs")
STATE_DIR   = os.path.join(BASE_DIR, "state")
LOG_FILE    = os.path.join(LOGS_DIR,  "chunker.log")
PROGRESS_FILE = os.path.join(STATE_DIR, "progress.json")

for d in (CHUNKS_DIR, LOGS_DIR, STATE_DIR):
    os.makedirs(d, exist_ok=True)

# ── 日志 ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── 配置 ─────────────────────────────────────────────────────────────────────
try:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        CONFIG = json.load(f)
    MAX_CHUNK_CHARS = CONFIG["max_chunk_chars"]
except (OSError, KeyError, json.JSONDecodeError) as e:
    logger.warning("无法读取 config.json（%s），使用默认值 max_chunk_chars=4900", e)
    MAX_CHUNK_CHARS = 4900

# ── 章节标题正则 ─────────────────────────────────────────────────────────────
CHAPTER_RE = re.compile(
    r"^("
    r"第[零一二三四五六七八九十百千万\d]+[章节回卷篇部]"
    r"|Chapter\s*\d+"
    r"|卷[零一二三四五六七八九十百千万\d]+"
    r"|楔子|序章|序言|前言|引子"
    r"|番外.{0,20}"
    r"|尾声|终章|后记|后序"
    r"|上篇|下篇|上卷|下卷|中卷"
    r"|第[零一二三四五六七八九十百千万\d]+话"
    r")",
    re.MULTILINE,
)


# ── 编码检测 ─────────────────────────────────────────────────────────────────

def detect_encoding(path: str) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with open(path, encoding=enc) as f:
                f.read()
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    try:
        import chardet
        with open(path, "rb") as f:
            raw = f.read()
        result = chardet.detect(raw)
        enc = result.get("encoding") or "gb18030"
        logger.info("chardet 检测编码：%s（置信度 %.2f）", enc, result.get("confidence", 0))
        return enc
    except ImportError:
        logger.warning("chardet 未安装，回退 gb18030")
        return "gb18030"


def read_file(path: str) -> tuple[str, str]:
    enc = detect_encoding(path)
    with open(path, encoding=enc, errors="replace") as f:
        text = f.read()
    return text, enc


# ── 切分核心 ─────────────────────────────────────────────────────────────────

def split_by_chapters(text: str) -> list[tuple[str, str]]:
    """按章节标题切分，返回 [(chapter_hint, section_text), ...]。"""
    positions = [m.start() for m in CHAPTER_RE.finditer(text)]
    if not positions:
        return [("正文", text)]

    sections = []
    if positions[0] > 0:
        sections.append(("前言", text[: positions[0]]))

    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        section = text[pos:end]
        title_line = section.splitlines()[0].strip()[:40]
        sections.append((title_line, section))

    return sections


def split_by_paragraphs(text: str) -> list[str]:
    paras = re.split(r"\n{2,}", text)
    return [p.strip() for p in paras if p.strip()]


def split_by_sentences(text: str, max_chars: int) -> list[str]:
    parts = re.split(r"(?<=[。！？!?…])", text)
    chunks: list[str] = []
    buf = ""
    for part in parts:
        if len(buf) + len(part) <= max_chars:
            buf += part
        else:
            if buf:
                chunks.append(buf)
            while len(part) > max_chars:
                chunks.append(part[:max_chars])
                part = part[max_chars:]
            buf = part
    if buf:
        chunks.append(buf)
    return chunks


def make_chunks(text: str, max_chars: int) -> list[tuple[str, str]]:
    """三级切分：章节 → 段落 → 句子边界。返回 [(hint, chunk_text), ...]。"""
    result: list[tuple[str, str]] = []
    for hint, section_text in split_by_chapters(text):
        buf = ""
        for para in split_by_paragraphs(section_text):
            if len(buf) + len(para) + 1 <= max_chars:
                buf = (buf + "\n" + para).strip() if buf else para
            else:
                if buf:
                    result.append((hint, buf))
                    buf = ""
                if len(para) <= max_chars:
                    buf = para
                else:
                    for seg in split_by_sentences(para, max_chars):
                        result.append((hint, seg))
        if buf:
            result.append((hint, buf))
    return result


# ── state/progress.json ───────────────────────────────────────────────────────

def load_progress() -> dict:
    if os.path.isfile(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_progress(progress: dict) -> None:
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ── 主流程 ───────────────────────────────────────────────────────────────────

def process_file(input_path: str,
                 limit_chars: int | None,
                 limit_lines: int | None) -> None:

    if not os.path.isfile(input_path):
        logger.error("文件不存在：%s", input_path)
        sys.exit(1)

    abs_path    = os.path.abspath(input_path)
    source_name = os.path.splitext(os.path.basename(abs_path))[0]
    run_at      = datetime.datetime.now().isoformat()

    logger.info("输入文件：%s", abs_path)

    text, enc = read_file(abs_path)
    total_chars = len(text)
    logger.info("编码：%s  总字符：%d", enc, total_chars)

    # ── limit 截断 ──────────────────────────────────────────────────────────
    if limit_lines is not None:
        lines = text.splitlines(keepends=True)
        text = "".join(lines[:limit_lines])
        logger.info("--limit-lines %d：截断至 %d 字符", limit_lines, len(text))
    elif limit_chars is not None:
        text = text[:limit_chars]
        logger.info("--limit-chars %d：截断至 %d 字符", limit_chars, len(text))

    processed_chars = len(text)

    # ── 切分 ────────────────────────────────────────────────────────────────
    chunks = make_chunks(text, MAX_CHUNK_CHARS)
    logger.info("切分完成：%d 个 chunk（上限 %d 字/块）", len(chunks), MAX_CHUNK_CHARS)

    # ── 写出 chunk 文件 ──────────────────────────────────────────────────────
    char_cursor = 0
    written     = 0
    chunk_ids: list[str] = []

    for idx, (hint, chunk_text) in enumerate(chunks):
        chunk_id  = f"{source_name}_{idx + 1:04d}"
        txt_path  = os.path.join(CHUNKS_DIR, f"{chunk_id}.txt")
        meta_path = os.path.join(CHUNKS_DIR, f"{chunk_id}.meta.json")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(chunk_text)

        # 近似字符偏移
        search_start = max(0, char_cursor - 200)
        probe        = chunk_text[:min(50, len(chunk_text))]
        pos          = text.find(probe, search_start)
        if pos == -1:
            pos = char_cursor
        char_start  = pos
        char_end    = pos + len(chunk_text)
        char_cursor = char_end

        meta = {
            "chunk_id":    chunk_id,
            "source_file": os.path.basename(abs_path),
            "chapter_hint": hint,
            "char_start":  char_start,
            "char_end":    char_end,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        chunk_ids.append(chunk_id)
        written += 1

    logger.info("已写出 %d 个 chunk 到 %s", written, CHUNKS_DIR)

    # ── 更新 state/progress.json ─────────────────────────────────────────────
    progress = load_progress()
    progress["chunker"] = {
        "status":          "done",
        "run_at":          run_at,
        "source_file":     os.path.basename(abs_path),
        "encoding":        enc,
        "total_chars":     total_chars,
        "processed_chars": processed_chars,
        "limit_chars":     limit_chars,
        "limit_lines":     limit_lines,
        "max_chunk_chars": MAX_CHUNK_CHARS,
        "chunks_written":  written,
        "first_chunk_id":  chunk_ids[0]  if chunk_ids else None,
        "last_chunk_id":   chunk_ids[-1] if chunk_ids else None,
    }
    progress["last_updated"] = run_at
    save_progress(progress)
    logger.info("state/progress.json 已更新")

    print(f"\n完成！共生成 {written} 个 chunk")
    print(f"  输入：{os.path.basename(abs_path)}（{processed_chars:,} 字符"
          + ("，全量" if limit_chars is None and limit_lines is None
             else f"，limit={'chars:'+str(limit_chars) if limit_chars else 'lines:'+str(limit_lines)}")
          + "）")
    print(f"  输出：{CHUNKS_DIR}")
    print(f"  状态：{PROGRESS_FILE}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="中文长文本切分工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python Scripts/chunker.py raw/某书.txt
  python Scripts/chunker.py raw/某书.txt --limit-chars 50000
  python Scripts/chunker.py raw/某书.txt --limit-lines 500
""",
    )
    parser.add_argument("input", help="输入 txt 文件路径")
    parser.add_argument(
        "--limit-chars",
        type=int,
        default=None,
        metavar="N",
        help="只处理文本前 N 个字符（小样本测试用）",
    )
    parser.add_argument(
        "--limit-lines",
        type=int,
        default=None,
        metavar="N",
        help="只处理文本前 N 行（小样本测试用）",
    )

    args = parser.parse_args()

    if args.limit_chars is not None and args.limit_lines is not None:
        parser.error("--limit-chars 和 --limit-lines 不能同时使用")

    process_file(
        input_path=args.input,
        limit_chars=args.limit_chars,
        limit_lines=args.limit_lines,
    )


if __name__ == "__main__":
    main()
