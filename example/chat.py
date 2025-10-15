

from __future__ import annotations

import argparse
import os
from typing import Dict, List

from anthropic import Anthropic
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaMemoryTool20250818Command,
    BetaMessageParam,
)
from pydantic import TypeAdapter

try:
    from memorylake import MemoryTool, MemoryToolError
except ModuleNotFoundError:  # pragma: no cover - fallback when not installed
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from memorylake import MemoryTool, MemoryToolError  # type: ignore

# Claude memory tool requires the context management beta header (2025-06-27).
_BETA_FEATURES = ["context-management-2025-06-27"]
_COMMAND_ADAPTER = TypeAdapter(BetaMemoryTool20250818Command)

os.environ["ANTHROPIC_API_KEY"] = "ANTHROPIC_API_KEY"

os.environ["ANTHROPIC_MODEL"] = "claude-sonnet-4-5-20250929"

os.environ["ANTHROPIC_BASE_URL"] = "ANTHROPIC_BASE_URL"


def run_chat(
    api_key: str | None,
    base_url: str | None,
    model: str,
    memory_path: str,
) -> None:
    client = Anthropic(api_key=api_key, base_url=base_url)
    memory_tool = MemoryTool(base_path=memory_path)

    messages: List[BetaMessageParam] = []
    local_menu: Dict[str, str] = {
        "help": "显示命令",
        "memory-view": "查看路径内容",
        "memory-create": "创建文件",
        "memory-insert": "插入文本",
        "memory-replace": "字符串替换",
        "memory-delete": "删除路径",
        "memory-rename": "重命名",
        "memory-exists": "检查存在性",
        "memory-list": "列出目录",
        "memory-clear": "清空全部记忆",
        "memory-stats": "查看统计",
        "memory-exec": "执行原始工具命令",
    }

    print(
        f"🧠 Claude + MemoryTool 示例 (模型: {model}) · 输入 '/exit' 退出 "
        f"· 记忆目录: {os.path.abspath(memory_path)}/memories"
    )
    print("本地命令: /help")

    while True:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"/exit", "/quit"}:
            print("会话结束，再见！")
            break

        if user_input.startswith("/"):
            if _handle_local_command(user_input, memory_tool, local_menu):
                continue

        messages.append({"role": "user", "content": user_input})

        needs_follow_up = True
        while needs_follow_up:
            needs_follow_up = False

            response = client.beta.messages.create(
                model=model,
                max_tokens=1024,
                messages=messages,
                tools=[{"type": "memory_20250818", "name": "memory"}],
                betas=_BETA_FEATURES,
                tool_choice={"type": "auto"},
            )

            messages.append({"role": "assistant", "content": response.content})

            printed_header = False
            for block in response.content:
                if block.type == "text":
                    if not printed_header:
                        print("\nClaude:", end=" ")
                        printed_header = True
                    print(block.text)
                elif block.type == "tool_use" and block.name == "memory":
                    command = _COMMAND_ADAPTER.validate_python(block.input)
                    result_text = memory_tool.execute(command)

                    tool_result_block: BetaContentBlockParam = {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    }
                    messages.append({"role": "user", "content": [tool_result_block]})
                    needs_follow_up = True
                    printed_header = False
                    break


def _handle_local_command(
    raw: str,
    memory_tool: MemoryTool,
    menu: Dict[str, str],
) -> bool:
    command_line = raw[1:].strip()
    if not command_line:
        _print_menu(menu)
        return True

    parts = command_line.split()
    name = parts[0]
    args = parts[1:]

    try:
        if name == "help":
            _print_menu(menu)
        elif name == "memory-view":
            path = args[0] if args else _prompt("路径")
            view_range = None
            if len(args) >= 3:
                view_range = (int(args[1]), int(args[2]))
            else:
                range_input = _prompt("行范围(例如 1 10, 留空跳过)")
                if range_input:
                    tokens = range_input.replace(",", " ").split()
                    if len(tokens) == 2:
                        view_range = (int(tokens[0]), int(tokens[1]))
            print(memory_tool.view_path(path, view_range))
        elif name == "memory-create":
            path = args[0] if args else _prompt("路径")
            text = " ".join(args[1:]) if len(args) > 1 else _prompt("内容")
            memory_tool.create_file(path, text)
            print("已创建")
        elif name == "memory-insert":
            path = args[0] if args else _prompt("路径")
            line_index = int(args[1]) if len(args) > 1 else int(_prompt("行号"))
            text = " ".join(args[2:]) if len(args) > 2 else _prompt("文本")
            memory_tool.insert_line(path, line_index, text)
            print("已插入")
        elif name == "memory-replace":
            path = args[0] if args else _prompt("路径")
            old = args[1] if len(args) > 1 else _prompt("原文本")
            new = args[2] if len(args) > 2 else _prompt("新文本")
            memory_tool.replace_text(path, old, new)
            print("已替换")
        elif name == "memory-delete":
            path = args[0] if args else _prompt("路径")
            memory_tool.delete_path(path)
            print("已删除")
        elif name == "memory-rename":
            old = args[0] if args else _prompt("原路径")
            new = args[1] if len(args) > 1 else _prompt("新路径")
            memory_tool.rename_path(old, new)
            print("已重命名")
        elif name == "memory-exists":
            path = args[0] if args else _prompt("路径")
            exists = memory_tool.memory_exists(path)
            print("存在" if exists else "不存在")
        elif name == "memory-list":
            path = args[0] if args else "/memories"
            entries = memory_tool.list_memories(path)
            if not entries:
                print("(空)")
            else:
                for item in entries:
                    print(item)
        elif name == "memory-clear":
            memory_tool.clear_all()
            print("已清空")
        elif name == "memory-stats":
            for key, value in memory_tool.stats().items():
                print(f"{key}: {value}")
        elif name == "memory-exec":
            _run_exec_command(memory_tool, args)
        else:
            print("未知命令")
    except MemoryToolError as exc:
        print(f"错误: {exc}")
    except ValueError as exc:
        print(f"输入无效: {exc}")
    except Exception as exc:  # pragma: no cover - safety net
        print(f"错误: {exc}")
    return True


def _run_exec_command(memory_tool: MemoryTool, args: List[str]) -> None:
    command = args[0] if args else _prompt("命令(view/create/insert/str_replace/delete/rename)")
    extra = args[1:]
    payload: Dict[str, object] = {"command": command}

    if command == "view":
        path = extra[0] if extra else _prompt("路径")
        payload["path"] = path
        if len(extra) >= 3:
            payload["view_range"] = [int(extra[1]), int(extra[2])]
        else:
            range_input = _prompt("行范围(例如 1 10, 留空跳过)")
            if range_input:
                tokens = range_input.replace(",", " ").split()
                if len(tokens) == 2:
                    payload["view_range"] = [int(tokens[0]), int(tokens[1])]
    elif command == "create":
        path = extra[0] if extra else _prompt("路径")
        text = " ".join(extra[1:]) if len(extra) > 1 else _prompt("内容")
        payload.update({"path": path, "file_text": text})
    elif command == "insert":
        path = extra[0] if extra else _prompt("路径")
        index = int(extra[1]) if len(extra) > 1 else int(_prompt("行号"))
        text = " ".join(extra[2:]) if len(extra) > 2 else _prompt("文本")
        payload.update({"path": path, "insert_line": index, "insert_text": text})
    elif command == "str_replace":
        path = extra[0] if extra else _prompt("路径")
        old = extra[1] if len(extra) > 1 else _prompt("原文本")
        new = extra[2] if len(extra) > 2 else _prompt("新文本")
        payload.update({"path": path, "old_str": old, "new_str": new})
    elif command == "delete":
        path = extra[0] if extra else _prompt("路径")
        payload["path"] = path
    elif command == "rename":
        old = extra[0] if extra else _prompt("原路径")
        new = extra[1] if len(extra) > 1 else _prompt("新路径")
        payload.update({"old_path": old, "new_path": new})
    else:
        print("不支持的工具命令")
        return

    result = memory_tool.execute_tool_payload(payload)
    print(result)


def _print_menu(menu: Dict[str, str]) -> None:
    print("本地命令:")
    for key, desc in menu.items():
        print(f"/{key} - {desc}")
    print("/exit - 退出")


def _prompt(label: str) -> str:
    return input(f"{label}: ").strip()


def _parse_args() -> argparse.Namespace:
    default_model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    parser = argparse.ArgumentParser(description="Anthropic memory tool chat demo.")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="Anthropic API key (falls back to ANTHROPIC_API_KEY env).",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("ANTHROPIC_BASE_URL"),
        help="Anthropic API base URL (falls back to ANTHROPIC_BASE_URL env).",
    )
    parser.add_argument(
        "--model",
        default=default_model,
        help=f"Claude model identifier (default: {default_model}).",
    )
    parser.add_argument(
        "--memory-path",
        default=os.environ.get("MEMORY_BASE_PATH", "./memory"),
        help="Local directory used to persist memories (default: ./memory).",
    )
    args = parser.parse_args()
    if not args.api_key:
        parser.error(
            "Anthropic API key is required. Provide via --api-key or set ANTHROPIC_API_KEY."
        )
    return args


if __name__ == "__main__":
    args = _parse_args()
    run_chat(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        memory_path=args.memory_path,
    )
