#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory tool 适配器

将内部 BaseMemoryBackend 封装为 Anthropic BetaAbstractMemoryTool，
以便通过官方 tool_runner 接口自动处理记忆相关命令。
"""

from __future__ import annotations

from typing import Callable, Optional

from anthropic.lib.tools import BetaAbstractMemoryTool
from anthropic.types.beta import (
    BetaMemoryTool20250818CreateCommand,
    BetaMemoryTool20250818DeleteCommand,
    BetaMemoryTool20250818InsertCommand,
    BetaMemoryTool20250818RenameCommand,
    BetaMemoryTool20250818StrReplaceCommand,
    BetaMemoryTool20250818ViewCommand,
)

from .memory_backend import BaseMemoryBackend


class MemoryBackendTool(BetaAbstractMemoryTool):
    """使用 BaseMemoryBackend 实现的记忆工具。"""

    def __init__(
        self,
        backend: BaseMemoryBackend,
        auto_save_callback: Optional[Callable[[str, str, dict], None]] = None,
        tool_overrides: Optional[dict] = None,
    ) -> None:
        self._tool_overrides = tool_overrides
        super().__init__()
        self._backend = backend
        self._auto_save_callback = auto_save_callback

    def _auto_save(self, path: str, operation: str, extra: Optional[dict] = None) -> None:
        extra_data = extra or {}
        if self._auto_save_callback is not None:
            self._auto_save_callback(path, operation, extra_data)

    def to_dict(self):  # type: ignore[override]
        base_dict = super().to_dict()
        if self._tool_overrides:
            base_dict.update(self._tool_overrides)
        return base_dict

    def view(self, command: BetaMemoryTool20250818ViewCommand) -> str:
        view_range = tuple(command.view_range) if command.view_range else None
        return self._backend.view(command.path, view_range)

    def create(self, command: BetaMemoryTool20250818CreateCommand) -> str:
        self._backend.create(command.path, command.file_text)
        self._auto_save(command.path, "create", {"file_text": command.file_text})
        return f"文件 {command.path} 创建成功"

    def str_replace(self, command: BetaMemoryTool20250818StrReplaceCommand) -> str:
        self._backend.str_replace(command.path, command.old_str, command.new_str)
        self._auto_save(
            command.path,
            "str_replace",
            {"old_str": command.old_str, "new_str": command.new_str},
        )
        return f"文件 {command.path} 已更新"

    def insert(self, command: BetaMemoryTool20250818InsertCommand) -> str:
        self._backend.insert(command.path, command.insert_line, command.insert_text)
        self._auto_save(
            command.path,
            "insert",
            {"insert_line": command.insert_line, "insert_text": command.insert_text},
        )
        return f"已在文件 {command.path} 的第 {command.insert_line} 行插入内容"

    def delete(self, command: BetaMemoryTool20250818DeleteCommand) -> str:
        self._backend.delete(command.path)
        self._auto_save(command.path, "delete")
        return f"已删除 {command.path}"

    def rename(self, command: BetaMemoryTool20250818RenameCommand) -> str:
        self._backend.rename(command.old_path, command.new_path)
        self._auto_save(
            command.old_path,
            "rename",
            {"old_path": command.old_path, "new_path": command.new_path},
        )
        return f"已将 {command.old_path} 重命名为 {command.new_path}"

    def clear_all_memory(self) -> str:
        self._backend.clear_all_memory()
        return "所有记忆已清除"
