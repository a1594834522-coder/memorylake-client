#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记忆管理示例：展示如何在无需调用 Claude API 的情况下管理记忆文件。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

from claude_memory_sdk import FileSystemMemoryBackend
from claude_memory_sdk.exceptions import MemoryBackendError, MemoryFileOperationError, MemoryPathError


CommandHandler = Callable[[FileSystemMemoryBackend, argparse.Namespace], Optional[str]]


def _parse_range(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    try:
        start_text, end_text = value.split(":", 1)
        start_line = int(start_text)
        end_line = int(end_text) if end_text else -1
        return (start_line, end_line)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("行范围必须使用 start:end 格式，例如 1:20 或 10:-1") from exc


def _cmd_list(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    memories = backend.list_memories(args.path)
    if not memories:
        return "[系统] 当前没有记忆文件。"
    return "\n".join(memories)


def _cmd_view(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    view_range = _parse_range(args.range)
    return backend.view(args.path, view_range)


def _cmd_create(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    content: Optional[str] = args.text
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    if content is None:
        print("[提示] 未提供文本内容，将从标准输入读取。按 Ctrl+D 结束输入。")
        content = sys.stdin.read()

    backend.create(args.path, content)
    return f"[系统] 已创建 {args.path}"


def _cmd_replace(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    backend.str_replace(args.path, args.old, args.new)
    return f"[系统] 已更新 {args.path}"


def _cmd_insert(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    backend.insert(args.path, args.line, args.text)
    return f"[系统] 已在第 {args.line} 行插入内容"


def _cmd_delete(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    backend.delete(args.path)
    return f"[系统] 已删除 {args.path}"


def _cmd_rename(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    backend.rename(args.old_path, args.new_path)
    return f"[系统] 已将 {args.old_path} 重命名为 {args.new_path}"


def _cmd_exists(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    exists = backend.memory_exists(args.path)
    return "[系统] 目标存在。" if exists else "[系统] 未找到目标。"


def _cmd_stats(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    stats = backend.get_memory_stats()
    return json.dumps(stats, ensure_ascii=False, indent=2)


def _cmd_clear(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    backend.clear_all_memory()
    return "[系统] 所有记忆已清除。"


def _cmd_backup(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    backend.backup_memory(args.destination)
    return f"[系统] 已备份到 {args.destination}"


def _cmd_restore(backend: FileSystemMemoryBackend, args: argparse.Namespace) -> str:
    backend.restore_memory(args.source)
    return f"[系统] 已从 {args.source} 恢复记忆数据。"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Claude Memory SDK 记忆管理示例",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--base-path",
        default="./memory",
        help="记忆数据的根目录（将自动创建）",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_command(name: str, handler: CommandHandler, help_text: str, *aliases: str) -> argparse.ArgumentParser:
        cmd_parser = subparsers.add_parser(name, help=help_text, aliases=list(aliases))
        cmd_parser.set_defaults(handler=handler)
        return cmd_parser

    list_parser = add_command("list", _cmd_list, "列出指定目录下的所有记忆", "ls")
    list_parser.add_argument("--path", default="/memories", help="要列出的目录路径")

    view_parser = add_command("view", _cmd_view, "查看记忆内容")
    view_parser.add_argument("path", help="记忆路径（必须以 /memories 开头）")
    view_parser.add_argument("--range", help="可选的行范围，格式为 start:end，使用 -1 表示文件末尾")

    create_parser = add_command("create", _cmd_create, "创建新的记忆文件", "new")
    create_parser.add_argument("path", help="新文件路径（必须以 /memories 开头）")
    create_parser.add_argument("--text", help="直接提供文件内容")
    create_parser.add_argument("--file", help="从外部文件读取内容")

    replace_parser = add_command("replace", _cmd_replace, "在记忆中进行唯一字符串替换", "str-replace")
    replace_parser.add_argument("path")
    replace_parser.add_argument("old", help="待替换的原始文本（必须唯一）")
    replace_parser.add_argument("new", help="替换后的文本")

    insert_parser = add_command("insert", _cmd_insert, "在指定行插入文本")
    insert_parser.add_argument("path")
    insert_parser.add_argument("line", type=int, help="插入行号（从 0 开始）")
    insert_parser.add_argument("text", help="要插入的文本")

    delete_parser = add_command("delete", _cmd_delete, "删除记忆文件或目录", "rm")
    delete_parser.add_argument("path")

    rename_parser = add_command("rename", _cmd_rename, "重命名或移动记忆路径", "mv")
    rename_parser.add_argument("old_path")
    rename_parser.add_argument("new_path")

    exists_parser = add_command("exists", _cmd_exists, "检查记忆路径是否存在")
    exists_parser.add_argument("path")

    add_command("stats", _cmd_stats, "显示记忆统计信息")
    add_command("clear", _cmd_clear, "清除所有记忆数据")

    backup_parser = add_command("backup", _cmd_backup, "导出记忆数据到压缩包")
    backup_parser.add_argument("destination", help="备份文件路径（推荐使用 .zip 扩展名）")

    restore_parser = add_command("restore", _cmd_restore, "从备份包恢复记忆数据")
    restore_parser.add_argument("source", help="备份文件路径")

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    backend = FileSystemMemoryBackend(base_path=args.base_path)

    try:
        handler: CommandHandler = args.handler  # type: ignore[attr-defined]
        output = handler(backend, args)
        if output:
            print(output)
    except (MemoryPathError, MemoryFileOperationError, MemoryBackendError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n已取消操作。", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
