#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基础聊天示例：演示自动记忆工具调用与日志打印。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Union

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from memorylake_sdk import MemoryLakeClient


def _extract_tool_events(message: Dict[str, Union[str, List[Dict[str, object]]]]) -> List[str]:
    content = message.get("content")
    if not isinstance(content, list):
        return []

    events: List[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "tool_use" and block.get("name") == "memory":
            input_obj = block.get("input")
            if isinstance(input_obj, dict):
                command = input_obj.get("command", "unknown")
            else:
                command = "unknown"
            events.append(f"tool_use(memory:{command})")
        elif block_type == "tool_result":
            events.append("tool_result")
    return events


def _print_tool_activity(before: Sequence[Dict[str, object]], after: Sequence[Dict[str, object]]) -> None:
    events: List[str] = []
    for message in after[len(before) :]:
        events.extend(_extract_tool_events(message))

    if events:
        print(f"[调试] 检测到记忆工具事件: {', '.join(events)}")
    else:
        print("[调试] 本轮对话未触发记忆工具调用。")


def _print_memories(client: MemoryLakeClient) -> None:
    memories = client.list_memories()
    if not memories:
        print("[系统] 当前没有记忆文件。")
        return
    print(f"[系统] 当前记忆文件数量: {len(memories)}")
    for path in memories[:8]:
        print(f"  - {path}")
    if len(memories) > 8:
        print("  ... (更多文件已省略)")


def main() -> None:
    print("=== Memory Lake SDK 基础聊天示例 ===\n")
    print(f"Anthropic SDK 版本: {anthropic.__version__}\n")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("错误：未检测到 ANTHROPIC_API_KEY 环境变量，请先配置官方 API Key。")
        return

    client = MemoryLakeClient()

    print("指令说明：")
    print("  /exit            退出程序")
    print("  /clear           清除会话历史")
    print("  /memories        查看当前记忆文件")
    print("  /history         查看原始消息计数")
    print("  /help            显示帮助")
    print("普通文本将发送给 Claude，Claude 会自行决定是否调用记忆工具。\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in {"/exit", "exit", "quit"}:
            print("再见！")
            break
        if lowered in {"/help", "help"}:
            print("\n示例用法：")
            print("  尝试输入 “请记住我喜欢喝咖啡” 等话语，观察是否触发记忆写入。")
            print("  使用 /memories 查看 ./memory 目录下的文件变化。\n")
            continue
        if lowered == "/clear":
            client.clear_conversation_history()
            print("[系统] 对话历史已清除。")
            continue
        if lowered == "/memories":
            _print_memories(client)
            continue
        if lowered == "/history":
            history = client.get_conversation_history()
            print(f"[系统] 会话消息总数: {len(history)}")
            continue

        history_before = client.get_conversation_history()

        try:
            reply = client.chat(user_input)
        except Exception as exc:  # pragma: no cover - 网络异常
            print(f"系统: 对话失败，请检查网络或 API 配置。错误信息: {exc}")
            continue

        print(f"Claude: {reply}")

        history_after = client.get_conversation_history()
        _print_tool_activity(history_before, history_after)


if __name__ == "__main__":
    main()
