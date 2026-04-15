"""
generate_from_prompt_lmstudio.py
读取现成 prompt 文本，通过 LM Studio 的 OpenAI 兼容接口生成正文，并写入指定输出文件。

设计原则：
- 这是 prompt txt -> 正文 txt 的叶子脚本，不回头改 generation context builder 主逻辑。
- 复用现有 test_lmstudio.py 的 chat/completions 调用方式，只把它包装成可复用 CLI。
- endpoint / model 不硬编码在主逻辑里，优先从 CLI、环境变量、STATE.json、config.json 读取。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests


# 此脚本只需两个路径（STATE.json、config.json），直接从 BASE_DIR 推导，保持 pathlib 风格。
# 其余路径常量的权威来源：Scripts/paths.py（os.path 风格，三层资产索引）。
BASE_DIR = Path(__file__).resolve().parent.parent
STATE_PATH = BASE_DIR / "STATE.json"
CONFIG_PATH = BASE_DIR / "config.json"


def load_json_file(path: Path) -> dict[str, Any]:
    """安全读取 JSON 文件；读取失败时返回空 dict，避免把状态读取问题变成崩溃。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def resolve_api_base(cli_value: str) -> str:
    """
    endpoint 优先级：
    CLI > 环境变量 > STATE.json > config.json
    这样既能复用当前工程配置，也不需要把接口地址硬编码进脚本。
    """
    if cli_value:
        return cli_value

    env_value = os.environ.get("LM_STUDIO_API_BASE") or os.environ.get("OPENAI_API_BASE")
    if env_value:
        return env_value

    state_data = load_json_file(STATE_PATH)
    state_api_base = state_data.get("model_config", {}).get("api_base")
    if state_api_base:
        return str(state_api_base)

    config_data = load_json_file(CONFIG_PATH)
    config_api_base = config_data.get("base_url")
    if config_api_base:
        return str(config_api_base)

    raise ValueError("未找到可用的 API base；请传 --api-base，或在 STATE.json/config.json/环境变量中配置。")


def resolve_model_name(cli_value: str) -> str:
    """
    model 优先级：
    CLI > 环境变量 > STATE.json > config.json
    保持与现有工程配置对齐，同时允许 A/B 实验显式覆写模型名。
    """
    if cli_value:
        return cli_value

    env_value = os.environ.get("LM_STUDIO_MODEL") or os.environ.get("OPENAI_MODEL")
    if env_value:
        return env_value

    state_data = load_json_file(STATE_PATH)
    model_config = state_data.get("model_config", {})
    state_model = model_config.get("active_local_model") or model_config.get("preferred_local_model")
    if state_model:
        return str(state_model)

    config_data = load_json_file(CONFIG_PATH)
    config_model = config_data.get("model")
    if config_model:
        return str(config_model)

    raise ValueError("未找到可用的 model；请传 --model，或在 STATE.json/config.json/环境变量中配置。")


def read_prompt_file(prompt_file: Path) -> str:
    """读取 UTF-8 prompt 文件，并做最小输入校验。"""
    if not prompt_file.exists():
        raise FileNotFoundError(f"prompt 文件不存在: {prompt_file}")
    if not prompt_file.is_file():
        raise ValueError(f"prompt 路径不是文件: {prompt_file}")

    prompt_text = prompt_file.read_text(encoding="utf-8").strip()
    if not prompt_text:
        raise ValueError(f"prompt 文件为空或只含空白: {prompt_file}")
    return prompt_text


def extract_message_content(data: dict[str, Any]) -> str:
    """
    兼容 OpenAI 兼容接口里最常见的 choices[0].message.content 结构。
    若后端返回 content list，则拼接 text 片段，避免把非空响应误判为空。
    """
    choices = data.get("choices") or []
    if not choices:
        return ""

    message = choices[0].get("message") or {}
    content = message.get("content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
        return "".join(parts).strip()

    return ""


def generate_text(
    prompt_text: str,
    api_base: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """把整份 prompt 作为一次完整 user 输入发送给 LM Studio。"""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt_text,
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(
        f"{api_base.rstrip('/')}/chat/completions",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    text = extract_message_content(response.json())
    if not text:
        raise ValueError("模型返回空字符串，未生成可保存正文。")
    return text


def write_output_file(output_file: Path, text: str) -> None:
    """输出目录不存在时自动创建，正文统一按 UTF-8 落盘。"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="读取 prompt 文本并通过 LM Studio 生成正文")
    parser.add_argument("--prompt-file", required=True, metavar="FILE", help="输入 prompt 文本文件（UTF-8）")
    parser.add_argument("--output-file", required=True, metavar="FILE", help="生成正文输出文件（UTF-8）")
    parser.add_argument("--model", default="", metavar="MODEL", help="可选模型名；默认按 STATE.json/config.json/环境变量解析")
    parser.add_argument("--temperature", type=float, default=0.7, metavar="FLOAT", help="采样温度，默认 0.7")
    parser.add_argument("--max-tokens", type=int, default=1200, metavar="INT", help="最大生成 token，默认 1200")
    parser.add_argument("--api-base", default="", metavar="URL", help="可选 API base；默认按 STATE.json/config.json/环境变量解析")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        prompt_file = Path(args.prompt_file).resolve()
        output_file = Path(args.output_file).resolve()
        prompt_text = read_prompt_file(prompt_file)
        api_base = resolve_api_base(args.api_base)
        model = resolve_model_name(args.model)
        generated_text = generate_text(
            prompt_text=prompt_text,
            api_base=api_base,
            model=model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        write_output_file(output_file, generated_text)
    except Exception as exc:
        print(f"错误：{exc}")
        sys.exit(1)

    print("[generate_from_prompt_lmstudio] success")
    print(f"  prompt_file: {prompt_file}")
    print(f"  output_file: {output_file}")
    print(f"  model: {model}")
    print(f"  api_base: {api_base}")


if __name__ == "__main__":
    main()
