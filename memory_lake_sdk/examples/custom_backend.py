#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自定义后端示例：实现一个内存中的记忆存储后端。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from memory_lake_sdk import BaseMemoryBackend
from memory_lake_sdk.exceptions import MemoryBackendError, MemoryFileOperationError, MemoryPathError


class InMemoryBackend(BaseMemoryBackend):
    """简单的内存后端实现，适合演示与测试。"""

    def __init__(self) -> None:
        self._files: Dict[str, str] = {}

    def _normalize_path(self, path: str) -> str:
        if not path.startswith("/memories"):
            raise MemoryPathError("路径必须以 /memories 开头")
        normalized = path.rstrip("/")
        return normalized if normalized else "/memories"

    def _list_children(self, directory: str) -> List[str]:
        prefix = directory.rstrip("/") + "/"
        children = set()
        for path in self._files:
            if not path.startswith(prefix):
                continue
            remainder = path[len(prefix) :]
            if not remainder:
                continue
            child = remainder.split("/", 1)[0]
            if "/" in remainder:
                children.add(child + "/")
            else:
                children.add(child)
        return sorted(children)

    def view(self, path: str, view_range: Optional[Tuple[int, int]] = None) -> str:
        normalized = self._normalize_path(path)
        if normalized == "/memories" or normalized not in self._files:
            children = self._list_children(normalized)
            if not children:
                return "该目录为空。"
            return "\n".join(children)

        content = self._files[normalized]
        lines = content.splitlines()
        if view_range:
            start, end = view_range
            start_idx = max(start - 1, 0)
            end_idx = None if end == -1 else end
            lines = lines[start_idx:end_idx]
            start_number = start_idx + 1
        else:
            start_number = 1
        return "\n".join(f"{i + start_number:4d}: {line}" for i, line in enumerate(lines))

    def create(self, path: str, file_text: str) -> None:
        normalized = self._normalize_path(path)
        if normalized == "/memories":
            raise MemoryFileOperationError("不能覆盖 /memories 根目录")
        self._files[normalized] = file_text

    def str_replace(self, path: str, old_str: str, new_str: str) -> None:
        normalized = self._normalize_path(path)
        if normalized not in self._files:
            raise MemoryFileOperationError(f"文件不存在: {path}")
        content = self._files[normalized]
        count = content.count(old_str)
        if count == 0:
            raise MemoryFileOperationError("未找到需要替换的文本")
        if count > 1:
            raise MemoryFileOperationError(f"文本出现 {count} 次，必须唯一")
        self._files[normalized] = content.replace(old_str, new_str)

    def insert(self, path: str, insert_line: int, insert_text: str) -> None:
        normalized = self._normalize_path(path)
        if normalized not in self._files:
            raise MemoryFileOperationError(f"文件不存在: {path}")
        lines = self._files[normalized].splitlines()
        if insert_line < 0 or insert_line > len(lines):
            raise MemoryFileOperationError("插入行号超出范围")
        lines.insert(insert_line, insert_text.rstrip("\n"))
        self._files[normalized] = "\n".join(lines)

    def delete(self, path: str) -> None:
        normalized = self._normalize_path(path)
        if normalized == "/memories":
            raise MemoryPathError("不能删除根目录")
        if normalized in self._files:
            del self._files[normalized]
            return
        prefix = normalized.rstrip("/") + "/"
        removed = [p for p in self._files if p.startswith(prefix)]
        if not removed:
            raise MemoryFileOperationError(f"路径不存在: {path}")
        for p in removed:
            del self._files[p]

    def rename(self, old_path: str, new_path: str) -> None:
        old_normalized = self._normalize_path(old_path)
        new_normalized = self._normalize_path(new_path)
        if new_normalized in self._files:
            raise MemoryFileOperationError(f"目标路径已存在: {new_path}")
        if old_normalized in self._files:
            self._files[new_normalized] = self._files.pop(old_normalized)
            return
        prefix = old_normalized.rstrip("/") + "/"
        matches = [p for p in self._files if p.startswith(prefix)]
        if not matches:
            raise MemoryFileOperationError(f"路径不存在: {old_path}")
        new_prefix = new_normalized.rstrip("/") + "/"
        for old_key in matches:
            suffix = old_key[len(prefix) :]
            self._files[new_prefix + suffix] = self._files.pop(old_key)

    def clear_all_memory(self) -> None:
        self._files.clear()

    def memory_exists(self, path: str) -> bool:
        normalized = self._normalize_path(path)
        if normalized in self._files:
            return True
        prefix = normalized.rstrip("/") + "/"
        return any(p.startswith(prefix) for p in self._files)

    def list_memories(self, path: str = "/memories") -> List[str]:
        directory = self._normalize_path(path)
        if directory != "/memories" and directory not in self._files:
            prefix = directory.rstrip("/") + "/"
            if not any(p.startswith(prefix) for p in self._files):
                raise MemoryFileOperationError(f"路径不存在: {path}")
        items: List[str] = []
        for entry in self._list_children(directory):
            items.append(f"{directory}/{entry}".replace("//", "/"))
        if directory in self._files:
            items.insert(0, directory)
        return items

    def get_memory_stats(self) -> Dict[str, object]:
        total_size = sum(len(content.encode("utf-8")) for content in self._files.values())
        return {
            "total_files": len(self._files),
            "total_directories": len({p.rsplit("/", 1)[0] for p in self._files}) if self._files else 0,
            "total_size_bytes": total_size,
        }

    def backup_memory(self, backup_path: str) -> None:
        path = Path(backup_path)
        payload = {"files": self._files}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def restore_memory(self, backup_path: str) -> None:
        path = Path(backup_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        files = data.get("files")
        if not isinstance(files, dict):
            raise MemoryBackendError("备份文件格式无效")
        self._files = {self._normalize_path(k): str(v) for k, v in files.items()}


def _demo_backend(backend: InMemoryBackend) -> None:
    print(">>> 创建用户偏好")
    backend.create(
        "/memories/preferences.xml",
        "<preferences>\n  <name>Alice</name>\n  <language>中文</language>\n</preferences>",
    )
    print(backend.view("/memories/preferences.xml"))

    print("\n>>> 插入补充信息")
    backend.insert("/memories/preferences.xml", 2, "  <favorite_drink>咖啡</favorite_drink>")
    print(backend.view("/memories/preferences.xml"))

    print("\n>>> 统计信息")
    print(json.dumps(backend.get_memory_stats(), ensure_ascii=False, indent=2))

    print("\n>>> 备份数据")
    backup_path = Path("in_memory_backup.json")
    backend.backup_memory(str(backup_path))
    print(f"备份已写入 {backup_path}")

    print("\n>>> 清空并恢复")
    backend.clear_all_memory()
    backend.restore_memory(str(backup_path))
    print(backend.view("/memories/preferences.xml"))


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="演示如何实现并使用自定义的内存记忆后端。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--with-client",
        action="store_true",
        help="尝试使用 MemoryLakeClient 加载自定义后端（需要 ANTHROPIC_API_KEY）",
    )
    args = parser.parse_args(argv)

    backend = InMemoryBackend()
    try:
        _demo_backend(backend)
    except (MemoryBackendError, MemoryFileOperationError, MemoryPathError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        sys.exit(1)

    if args.with_client:
        from memory_lake_sdk import MemoryLakeClient

        try:
            client = MemoryLakeClient(memory_backend=backend, auto_save_memory=False)
        except ValueError as exc:
            print(f"[提示] 创建 MemoryLakeClient 失败：{exc}", file=sys.stderr)
            print("       请设置 ANTHROPIC_API_KEY 环境变量后重试。", file=sys.stderr)
            return

        print("\n>>> 使用 MemoryLakeClient 操作自定义后端")
        client.add_memory("/memories/session.txt", "MemoryLakeClient 已连接到自定义后端。")
        print(client.get_memory("/memories/session.txt"))


if __name__ == "__main__":
    main()
