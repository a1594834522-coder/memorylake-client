"""
Claude Memory Server 记忆管理器
"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional


class MemoryManager:
    """文件系统记忆管理器"""

    def __init__(self, base_path: str = "./memory"):
        """
        初始化记忆管理器

        Args:
            base_path: 记忆存储基础路径
        """
        self.base_path = Path(base_path)
        self.memory_root = self.base_path / "memories"
        self.memory_root.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: str) -> Path:
        """
        验证并解析记忆路径

        Args:
            path: 记忆路径

        Returns:
            解析后的Path对象

        Raises:
            ValueError: 路径无效或不安全
        """
        if not path.startswith("/memories"):
            raise ValueError(f"Path must start with /memories, got: {path}")

        relative_path = path[len("/memories"):].lstrip("/")
        full_path = self.memory_root / relative_path if relative_path else self.memory_root

        try:
            # 确保路径在允许的目录内
            full_path.resolve().relative_to(self.memory_root.resolve())
        except ValueError as e:
            raise ValueError(f"Path {path} would escape /memories directory") from e

        return full_path

    def view_directory(self) -> str:
        """
        查看记忆目录内容

        Returns:
            目录内容字符串
        """
        items: List[str] = []
        try:
            for item in sorted(self.memory_root.iterdir()):
                if item.name.startswith("."):
                    continue
                items.append(f"{item.name}/" if item.is_dir() else item.name)
            return f"Directory: /memories\n" + "\n".join([f"- {item}" for item in items])
        except Exception as e:
            raise RuntimeError(f"Cannot read memory directory: {e}")

    def view_file(self, file_path: str, view_range: Optional[List[int]] = None) -> str:
        """
        查看文件内容

        Args:
            file_path: 文件路径
            view_range: 可选的行范围 [start, end]

        Returns:
            文件内容字符串
        """
        full_path = self._validate_path(file_path)

        if not full_path.is_file():
            raise RuntimeError(f"File not found: {file_path}")

        try:
            content = full_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            if view_range:
                start_line = max(1, view_range[0]) - 1
                end_line = len(lines) if view_range[1] == -1 else view_range[1]
                lines = lines[start_line:end_line]
                start_num = start_line + 1
            else:
                start_num = 1

            numbered_lines = [f"{i + start_num:4d}: {line}" for i, line in enumerate(lines)]
            return "\n".join(numbered_lines)
        except Exception as e:
            raise RuntimeError(f"Cannot read file {file_path}: {e}")

    def create_file(self, file_path: str, content: str) -> str:
        """
        创建新文件

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            操作结果消息
        """
        full_path = self._validate_path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"File created successfully at {file_path}"

    def str_replace(self, file_path: str, old_str: str, new_str: str) -> str:
        """
        替换文件中的文本

        Args:
            file_path: 文件路径
            old_str: 要替换的文本
            new_str: 新文本

        Returns:
            操作结果消息
        """
        full_path = self._validate_path(file_path)

        if not full_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = full_path.read_text(encoding="utf-8")
        count = content.count(old_str)
        if count == 0:
            raise ValueError(f"Text not found in {file_path}")
        elif count > 1:
            raise ValueError(f"Text appears {count} times in {file_path}. Must be unique.")

        new_content = content.replace(old_str, new_str)
        full_path.write_text(new_content, encoding="utf-8")
        return f"File {file_path} has been edited"

    def insert_text(self, file_path: str, insert_line: int, insert_text: str) -> str:
        """
        在指定行插入文本

        Args:
            file_path: 文件路径
            insert_line: 插入行号
            insert_text: 要插入的文本

        Returns:
            操作结果消息
        """
        full_path = self._validate_path(file_path)

        if not full_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        lines = full_path.read_text(encoding="utf-8").splitlines()
        if insert_line < 0 or insert_line > len(lines):
            raise ValueError(f"Invalid insert_line {insert_line}. Must be 0-{len(lines)}")

        lines.insert(insert_line, insert_text.rstrip("\n"))
        full_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return f"Text inserted at line {insert_line} in {file_path}"

    def delete_path(self, path: str) -> str:
        """
        删除文件或目录

        Args:
            path: 要删除的路径

        Returns:
            操作结果消息
        """
        full_path = self._validate_path(path)

        if path == "/memories":
            raise ValueError("Cannot delete the /memories directory itself")

        if full_path.is_file():
            full_path.unlink()
            return f"File deleted: {path}"
        elif full_path.is_dir():
            shutil.rmtree(full_path)
            return f"Directory deleted: {path}"
        else:
            raise FileNotFoundError(f"Path not found: {path}")

    def rename_path(self, old_path: str, new_path: str) -> str:
        """
        重命名或移动文件/目录

        Args:
            old_path: 源路径
            new_path: 目标路径

        Returns:
            操作结果消息
        """
        old_full_path = self._validate_path(old_path)
        new_full_path = self._validate_path(new_path)

        if not old_full_path.exists():
            raise FileNotFoundError(f"Source path not found: {old_path}")
        if new_full_path.exists():
            raise ValueError(f"Destination already exists: {new_path}")

        new_full_path.parent.mkdir(parents=True, exist_ok=True)
        old_full_path.rename(new_full_path)
        return f"Renamed {old_path} to {new_path}"

    def clear_all_memory(self) -> str:
        """
        清除所有记忆

        Returns:
            操作结果消息
        """
        if self.memory_root.exists():
            shutil.rmtree(self.memory_root)
        self.memory_root.mkdir(parents=True, exist_ok=True)
        return "All memory cleared"

    def get_memory_files(self) -> List[str]:
        """
        获取所有记忆文件列表

        Returns:
            记忆文件名列表
        """
        try:
            result = self.view_directory()
            lines = result.split('\n')
            files = []
            for line in lines[1:]:  # Skip first line (directory header)
                if line.strip().startswith('- '):
                    file_name = line.strip()[2:]
                    if not file_name.endswith('/'):
                        files.append(file_name)
            return files
        except Exception:
            return []

    def get_memory_stats(self) -> dict:
        """
        获取记忆统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "total_files": 0,
            "total_size": 0,
            "directories": 0,
            "last_modified": None
        }

        try:
            if self.memory_root.exists():
                for item in self.memory_root.rglob("*"):
                    if item.is_file():
                        stats["total_files"] += 1
                        stats["total_size"] += item.stat().st_size
                        if not stats["last_modified"] or item.stat().st_mtime > stats["last_modified"]:
                            stats["last_modified"] = item.stat().st_mtime
                    elif item.is_dir():
                        stats["directories"] += 1

                # 转换时间戳为可读格式
                if stats["last_modified"]:
                    stats["last_modified"] = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(stats["last_modified"])
                    )
        except Exception:
            pass

        return stats