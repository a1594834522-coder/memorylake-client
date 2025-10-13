#!/usr/bin/env python3
"""Quick utility to show which model Anthropic actually runs."""

import os
import sys
from pathlib import Path

# Ensure the project root is importable when running from source.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

os.environ["ANTHROPIC_API_KEY"] = "xxx"

os.environ["ANTHROPIC_MODEL"] = "claude-sonnet-4-5"

os.environ["ANTHROPIC_BASE_URL"] = "xxx"

from memorylake_sdk import MemoryLakeClient


def main() -> None:
    client = MemoryLakeClient()
    print(f"Configured model (client.model): {client.model}")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY 未设置，跳过真实 API 调用。")
        return

    anthropic_client = client.client
    try:
        response = anthropic_client.beta.messages.create(
            model=client.model,
            max_tokens=1,
            messages=[{"role": "user", "content": "你是什么模型？"}],
        )
    except Exception as exc:
        print(f"调用 beta.messages.create 失败: {exc}")
        return

    api_model = getattr(response, "model", None)
    if api_model:
        print(f"Model reported by API: {api_model}")
    else:
        print("API 调用成功，但未返回 model 字段。")

    reply_text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    if reply_text:
        print(f"Assistant reply: {reply_text}")


if __name__ == "__main__":
    main()
