#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义后端示例

演示如何创建自定义的记忆存储后端。
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Any, List, Dict

# 添加父目录到路径，以便导入claude_memory_sdk
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_memory_sdk import ClaudeMemoryClient
from claude_memory_sdk.memory_backend import BaseMemoryBackend
from claude_memory_sdk.exceptions import MemoryBackendError, MemoryPathError, MemoryFileOperationError


class InMemoryBackend(BaseMemoryBackend):
    """内存记忆后端实现

    将记忆存储在内存中，适合临时使用和测试。
    """

    def __init__(self):
        """初始化内存后端"""
        self._storage: Dict[str, str] = {}
        print("内存后端初始化完成")

    def _validate_path(self, path: str) -> str:
        """验证路径格式"""
        if not path.startswith('/memories'):
            raise MemoryPathError(f"路径必须以 /memories 开头，得到: {path}")
        return path

    def view(self, path: str, view_range: Optional[Tuple[int, int]] = None) -> str:
        """查看记忆内容"""
        normalized_path = self._validate_path(path)

        if normalized_path == '/memories':
            # 返回所有记忆的列表
            if not self._storage:
                return "Directory: /memories\n(空)"

            items = []
            for stored_path in sorted(self._storage.keys()):
                # 提取相对路径
                relative_path = stored_path[len('/memories'):].lstrip('/')
                items.append(relative_path)

            result = f"Directory: /memories\n" + "\n".join([f"- {item}" for item in items])
            return result

        if normalized_path not in self._storage:
            raise MemoryFileOperationError(f"记忆不存在: {path}")

        content = self._storage[normalized_path]
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

    def create(self, path: str, file_text: str) -> None:
        """创建新记忆"""
        normalized_path = self._validate_path(path)

        if normalized_path in self._storage:
            raise MemoryFileOperationError(f"记忆已存在: {path}")

        self._storage[normalized_path] = file_text

    def str_replace(self, path: str, old_str: str, new_str: str) -> None:
        """替换记忆内容"""
        normalized_path = self._validate_path(path)

        if normalized_path not in self._storage:
            raise MemoryFileOperationError(f"记忆不存在: {path}")

        content = self._storage[normalized_path]
        count = content.count(old_str)

        if count == 0:
            raise MemoryFileOperationError(f"在 {path} 中未找到指定文本")
        elif count > 1:
            raise MemoryFileOperationError(f"文本在 {path} 中出现 {count} 次，必须唯一")

        new_content = content.replace(old_str, new_str)
        self._storage[normalized_path] = new_content

    def insert(self, path: str, insert_line: int, insert_text: str) -> None:
        """插入内容到指定行"""
        normalized_path = self._validate_path(path)

        if normalized_path not in self._storage:
            raise MemoryFileOperationError(f"记忆不存在: {path}")

        lines = self._storage[normalized_path].splitlines()

        if insert_line < 0 or insert_line > len(lines):
            raise MemoryFileOperationError(f"无效的插入行号 {insert_line}，必须在 0-{len(lines)} 之间")

        lines.insert(insert_line, insert_text.rstrip('\n'))
        self._storage[normalized_path] = '\n'.join(lines) + '\n'

    def delete(self, path: str) -> None:
        """删除记忆"""
        normalized_path = self._validate_path(path)

        if normalized_path == '/memories':
            raise MemoryPathError("不能删除 /memories 目录本身")

        if normalized_path not in self._storage:
            raise MemoryFileOperationError(f"记忆不存在: {path}")

        del self._storage[normalized_path]

    def rename(self, old_path: str, new_path: str) -> None:
        """重命名记忆"""
        old_normalized = self._validate_path(old_path)
        new_normalized = self._validate_path(new_path)

        if old_normalized not in self._storage:
            raise MemoryFileOperationError(f"源记忆不存在: {old_path}")

        if new_normalized in self._storage:
            raise MemoryFileOperationError(f"目标记忆已存在: {new_path}")

        self._storage[new_normalized] = self._storage[old_normalized]
        del self._storage[old_normalized]

    def clear_all_memory(self) -> None:
        """清除所有记忆"""
        self._storage.clear()

    def memory_exists(self, path: str) -> bool:
        """检查记忆是否存在"""
        try:
            normalized_path = self._validate_path(path)
            return normalized_path in self._storage
        except MemoryPathError:
            return False

    def list_memories(self, path: str = "/memories") -> List[str]:
        """列出所有记忆"""
        normalized_path = self._validate_path(path)

        if normalized_path != '/memories':
            raise MemoryFileOperationError("只能列出 /memories 目录")

        return list(self._storage.keys())

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_files": len(self._storage),
            "total_directories": 0,
            "total_size_bytes": sum(len(content) for content in self._storage.values()),
            "largest_file": None,
            "largest_file_size": 0,
            "file_types": {},
        }

        if self._storage:
            for path, content in self._storage.items():
                size = len(content)
                if size > stats["largest_file_size"]:
                    stats["largest_file_size"] = size
                    stats["largest_file"] = path

                # 统计文件类型
                if '.' in path:
                    suffix = '.' + path.split('.')[-1]
                    stats["file_types"][suffix] = stats["file_types"].get(suffix, 0) + 1
                else:
                    stats["file_types"]["无扩展名"] = stats["file_types"].get("无扩展名", 0) + 1

        return stats

    def backup_memory(self, backup_path: str) -> None:
        """备份记忆数据"""
        import json

        backup_data = {
            "version": "1.0",
            "timestamp": str(Path().cwd()),
            "memories": self._storage
        }

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

    def restore_memory(self, backup_path: str) -> None:
        """恢复记忆数据"""
        import json

        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        if backup_data.get("version") != "1.0":
            raise MemoryFileOperationError("不支持的备份版本")

        self._storage = backup_data.get("memories", {})


def main():
    """主函数 - 自定义后端示例"""
    print("=== Claude Memory SDK 自定义后端示例 ===\n")

    try:
        # 创建自定义后端
        print("1. 创建内存后端...")
        backend = InMemoryBackend()

        # 使用自定义后端初始化客户端
        print("2. 初始化客户端...")
        client = ClaudeMemoryClient(
            api_key="test-key",  # 使用测试密钥
            memory_backend=backend
        )
        print("[OK] 客户端初始化成功\n")

        # 测试记忆操作
        print("3. 测试记忆操作...")

        # 添加记忆
        client.add_memory("/memories/greeting.txt", "你好，世界！")
        client.add_memory("/memories/note.txt", "这是一个内存后端的测试。")
        client.add_memory("/memories/todo.txt", "待办事项:\n- 学习Python\n- 开发项目\n- 编写文档")

        print("[OK] 记忆添加成功")

        # 列出记忆
        memories = client.list_memories()
        print(f"内存中的记忆数: {len(memories)}")
        for memory in memories:
            print(f"  - {memory}")

        # 读取记忆
        print("\n4. 读取记忆内容...")
        greeting = client.get_memory("/memories/greeting.txt")
        print(f"问候内容: {greeting.strip()}")

        # 查看目录
        print("\n5. 查看记忆目录...")
        directory = client.get_memory("/memories")
        print("目录内容:")
        print(directory)

        # 更新记忆
        print("\n6. 更新记忆...")
        client.memory_backend.str_replace(
            "/memories/note.txt",
            "内存后端",
            "自定义内存后端"
        )
        updated_note = client.get_memory("/memories/note.txt")
        print(f"更新后的内容: {updated_note.strip()}")

        # 获取统计信息
        print("\n7. 获取统计信息...")
        stats = client.get_memory_stats()
        print("内存后端统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 备份和恢复
        print("\n8. 测试备份和恢复...")
        backup_file = "memory_backup.json"
        client.backup_memory(backup_file)
        print(f"[OK] 备份完成: {backup_file}")

        # 清除并恢复
        client.clear_all_memories()
        print("[OK] 记忆已清除")

        client.restore_memory(backup_file)
        print("[OK] 记忆已恢复")

        restored_count = len(client.list_memories())
        print(f"恢复后的记忆数: {restored_count}")

        print("\n=== 自定义后端示例完成 ===")
        print("内存后端功能正常!")

        return True

    except Exception as e:
        print(f"[ERROR] 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)