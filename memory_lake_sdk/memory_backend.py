#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Lake SDK 记忆存储后端

定义了记忆存储的抽象接口和具体的文件系统实现。
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any, List, Dict
from pathlib import Path
import shutil
import logging

from .exceptions import MemoryBackendError, MemoryPathError, MemoryFileOperationError

# 设置日志
logger = logging.getLogger(__name__)


class BaseMemoryBackend(ABC):
    """记忆存储后端抽象基类

    所有记忆存储后端必须继承此类并实现其抽象方法。
    这确保了不同存储实现之间的一致性接口。
    """

    @abstractmethod
    def view(self, path: str, view_range: Optional[Tuple[int, int]] = None) -> str:
        """查看路径内容（文件或目录）

        Args:
            path: 要查看的路径，必须以 '/memories' 开头
            view_range: 可选的行范围元组 (start_line, end_line)，
                       end_line 为 -1 表示到文件末尾

        Returns:
            路径的内容字符串

        Raises:
            MemoryPathError: 路径无效或不安全
            MemoryFileOperationError: 文件操作失败
        """
        pass

    @abstractmethod
    def create(self, path: str, file_text: str) -> None:
        """创建新文件

        Args:
            path: 要创建的文件路径，必须以 '/memories' 开头
            file_text: 文件内容

        Raises:
            MemoryPathError: 路径无效或不安全
            MemoryFileOperationError: 文件创建失败
        """
        pass

    @abstractmethod
    def str_replace(self, path: str, old_str: str, new_str: str) -> None:
        """字符串替换

        Args:
            path: 文件路径，必须以 '/memories' 开头
            old_str: 要替换的字符串
            new_str: 替换后的字符串

        Raises:
            MemoryPathError: 路径无效或不安全
            MemoryFileOperationError: 字符串替换失败
        """
        pass

    @abstractmethod
    def insert(self, path: str, insert_line: int, insert_text: str) -> None:
        """行插入

        Args:
            path: 文件路径，必须以 '/memories' 开头
            insert_line: 插入的行号（从0开始）
            insert_text: 要插入的文本

        Raises:
            MemoryPathError: 路径无效或不安全
            MemoryFileOperationError: 行插入失败
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        """删除路径

        Args:
            path: 要删除的路径，必须以 '/memories' 开头

        Raises:
            MemoryPathError: 路径无效或不安全
            MemoryFileOperationError: 删除操作失败
        """
        pass

    @abstractmethod
    def rename(self, old_path: str, new_path: str) -> None:
        """重命名/移动路径

        Args:
            old_path: 原路径，必须以 '/memories' 开头
            new_path: 新路径，必须以 '/memories' 开头

        Raises:
            MemoryPathError: 路径无效或不安全
            MemoryFileOperationError: 重命名操作失败
        """
        pass

    def clear_all_memory(self) -> None:
        """清除所有记忆数据

        默认实现抛出 NotImplementedError，子类可以选择性地实现。

        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("clear_all_memory not implemented")

    def memory_exists(self, path: str) -> bool:
        """检查记忆是否存在

        Args:
            path: 记忆文件或目录路径，必须以 '/memories' 开头

        Returns:
            如果记忆存在则返回 True，否则返回 False

        Raises:
            MemoryPathError: 路径无效或不安全
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("memory_exists not implemented")

    def list_memories(self, path: str = "/memories") -> List[str]:
        """列出指定目录下的所有记忆

        Args:
            path: 目录路径，必须以 '/memories' 开头，默认为根目录

        Returns:
            记忆文件和目录的路径列表

        Raises:
            MemoryPathError: 路径无效或不安全
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("list_memories not implemented")

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆存储统计信息

        Returns:
            包含统计信息的字典

        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("get_memory_stats not implemented")

    def backup_memory(self, backup_path: str) -> None:
        """备份记忆数据

        Args:
            backup_path: 备份文件路径

        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("backup_memory not implemented")

    def restore_memory(self, backup_path: str) -> None:
        """从备份恢复记忆数据

        Args:
            backup_path: 备份文件路径

        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("restore_memory not implemented")


class FileSystemMemoryBackend(BaseMemoryBackend):
    """基于文件系统的记忆存储后端实现

    使用本地文件系统存储记忆数据，包含严格的安全检查以防止路径遍历攻击。
    """

    def __init__(self, base_path: str = "./memory"):
        """初始化文件系统后端

        Args:
            base_path: 记忆存储的基础路径
        """
        self.base_path = Path(base_path).resolve()
        self.memory_root = self.base_path / "memories"

        # 确保记忆目录存在
        self.memory_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"文件系统记忆后端初始化完成，基础路径: {self.base_path}")

    def _get_safe_path(self, path: str) -> Path:
        """验证并解析路径，防止目录遍历攻击

        Args:
            path: 用户提供的路径

        Returns:
            验证后的安全路径

        Raises:
            MemoryPathError: 路径无效或不安全
        """
        if not path.startswith('/memories'):
            raise MemoryPathError(f"路径必须以 /memories 开头，得到: {path}")

        # 移除 /memories 前缀并清理路径
        relative_path = path[len('/memories'):].lstrip('/')

        # 如果相对路径为空，返回记忆根目录
        if not relative_path:
            return self.memory_root

        full_path = self.memory_root / relative_path

        try:
            # 解析为绝对路径并确保其在记忆根目录内
            resolved_path = full_path.resolve()
            resolved_path.relative_to(self.memory_root.resolve())
        except ValueError as e:
            raise MemoryPathError(f"路径 {path} 会逃离 /memories 目录") from e

        return resolved_path

    def view(self, path: str, view_range: Optional[Tuple[int, int]] = None) -> str:
        """查看路径内容"""
        full_path = self._get_safe_path(path)

        if full_path.is_dir():
            # 返回目录内容列表
            items = []
            try:
                for item in sorted(full_path.iterdir()):
                    if item.name.startswith('.'):
                        continue
                    items.append(f"{item.name}/" if item.is_dir() else item.name)

                result = f"Directory: {path}\n" + "\n".join([f"- {item}" for item in items])
                logger.debug(f"查看目录 {path}，包含 {len(items)} 个项目")
                return result
            except Exception as e:
                raise MemoryFileOperationError(f"无法读取目录 {path}: {e}") from e

        elif full_path.is_file():
            # 返回文件内容
            try:
                content = full_path.read_text(encoding='utf-8')
                lines = content.splitlines()

                if view_range:
                    start_line = max(1, view_range[0]) - 1
                    end_line = len(lines) if view_range[1] == -1 else view_range[1]
                    lines = lines[start_line:end_line]
                    start_num = start_line + 1
                else:
                    start_num = 1

                numbered_lines = [f"{i + start_num:4d}: {line}" for i, line in enumerate(lines)]
                result = "\n".join(numbered_lines)
                logger.debug(f"查看文件 {path}，显示 {len(lines)} 行")
                return result
            except Exception as e:
                raise MemoryFileOperationError(f"无法读取文件 {path}: {e}") from e
        else:
            raise MemoryFileOperationError(f"路径不存在: {path}")

    def create(self, path: str, file_text: str) -> None:
        """创建新文件"""
        full_path = self._get_safe_path(path)

        try:
            # 确保父目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件内容
            full_path.write_text(file_text, encoding='utf-8')
            logger.info(f"创建文件: {path}")
        except Exception as e:
            raise MemoryFileOperationError(f"无法创建文件 {path}: {e}") from e

    def str_replace(self, path: str, old_str: str, new_str: str) -> None:
        """字符串替换"""
        full_path = self._get_safe_path(path)

        if not full_path.is_file():
            raise MemoryFileOperationError(f"文件不存在: {path}")

        try:
            content = full_path.read_text(encoding='utf-8')
            count = content.count(old_str)

            if count == 0:
                raise MemoryFileOperationError(f"在 {path} 中未找到指定文本")
            elif count > 1:
                raise MemoryFileOperationError(f"文本在 {path} 中出现 {count} 次，必须唯一")

            new_content = content.replace(old_str, new_str)
            full_path.write_text(new_content, encoding='utf-8')
            logger.info(f"替换文件 {path} 中的文本")
        except Exception as e:
            raise MemoryFileOperationError(f"无法替换文件 {path} 中的文本: {e}") from e

    def insert(self, path: str, insert_line: int, insert_text: str) -> None:
        """行插入"""
        full_path = self._get_safe_path(path)

        if not full_path.is_file():
            raise MemoryFileOperationError(f"文件不存在: {path}")

        try:
            lines = full_path.read_text(encoding='utf-8').splitlines()

            if insert_line < 0 or insert_line > len(lines):
                raise MemoryFileOperationError(f"无效的插入行号 {insert_line}，必须在 0-{len(lines)} 之间")

            lines.insert(insert_line, insert_text.rstrip('\n'))
            full_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            logger.info(f"在文件 {path} 的第 {insert_line} 行插入文本")
        except Exception as e:
            raise MemoryFileOperationError(f"无法在文件 {path} 中插入文本: {e}") from e

    def delete(self, path: str) -> None:
        """删除路径"""
        full_path = self._get_safe_path(path)

        # 防止删除记忆根目录
        if path == '/memories':
            raise MemoryPathError("不能删除 /memories 目录本身")

        try:
            if full_path.is_file():
                full_path.unlink()
                logger.info(f"删除文件: {path}")
            elif full_path.is_dir():
                shutil.rmtree(full_path)
                logger.info(f"删除目录: {path}")
            else:
                raise MemoryFileOperationError(f"路径不存在: {path}")
        except Exception as e:
            raise MemoryFileOperationError(f"无法删除 {path}: {e}") from e

    def rename(self, old_path: str, new_path: str) -> None:
        """重命名/移动路径"""
        old_full_path = self._get_safe_path(old_path)
        new_full_path = self._get_safe_path(new_path)

        if not old_full_path.exists():
            raise MemoryFileOperationError(f"源路径不存在: {old_path}")

        if new_full_path.exists():
            raise MemoryFileOperationError(f"目标路径已存在: {new_path}")

        try:
            # 确保目标父目录存在
            new_full_path.parent.mkdir(parents=True, exist_ok=True)
            old_full_path.rename(new_full_path)
            logger.info(f"重命名 {old_path} 为 {new_path}")
        except Exception as e:
            raise MemoryFileOperationError(f"无法重命名 {old_path} 为 {new_path}: {e}") from e

    def clear_all_memory(self) -> None:
        """清除所有记忆数据"""
        try:
            if self.memory_root.exists():
                shutil.rmtree(self.memory_root)
            self.memory_root.mkdir(parents=True, exist_ok=True)
            logger.info("已清除所有记忆数据")
        except Exception as e:
            raise MemoryFileOperationError(f"无法清除记忆数据: {e}") from e

    def memory_exists(self, path: str) -> bool:
        """检查记忆是否存在

        Args:
            path: 记忆文件或目录路径，必须以 '/memories' 开头

        Returns:
            如果记忆存在则返回 True，否则返回 False

        Raises:
            MemoryPathError: 路径无效或不安全
        """
        try:
            full_path = self._get_safe_path(path)
            return full_path.exists()
        except MemoryPathError:
            raise
        except Exception as e:
            logger.error(f"检查记忆存在性失败: {e}")
            raise MemoryFileOperationError(f"无法检查记忆 {path} 的存在性: {e}") from e

    def list_memories(self, path: str = "/memories") -> List[str]:
        """列出指定目录下的所有记忆

        Args:
            path: 目录路径，必须以 '/memories' 开头，默认为根目录

        Returns:
            记忆文件和目录的路径列表

        Raises:
            MemoryPathError: 路径无效或不安全
            MemoryFileOperationError: 操作失败
        """
        try:
            full_path = self._get_safe_path(path)
            if not full_path.is_dir():
                raise MemoryFileOperationError(f"路径不是目录: {path}")

            memories = []
            for item in sorted(full_path.rglob("*")):
                if item.name.startswith("."):
                    continue

                # 获取相对于记忆根目录的路径
                relative_path = item.relative_to(self.memory_root)
                memory_path = f"/memories/{relative_path}"

                if item.is_dir():
                    memory_path += "/"
                memories.append(memory_path)

            logger.debug(f"列出 {path} 下的记忆，共 {len(memories)} 个")
            return memories
        except MemoryPathError:
            raise
        except Exception as e:
            logger.error(f"列出记忆失败: {e}")
            raise MemoryFileOperationError(f"无法列出 {path} 下的记忆: {e}") from e

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆存储统计信息

        Returns:
            包含统计信息的字典
        """
        try:
            stats = {
                "total_files": 0,
                "total_directories": 0,
                "total_size_bytes": 0,
                "largest_file": None,
                "largest_file_size": 0,
                "file_types": {},
            }

            if not self.memory_root.exists():
                return stats

            for item in self.memory_root.rglob("*"):
                if item.name.startswith("."):
                    continue

                if item.is_file():
                    stats["total_files"] += 1
                    size = item.stat().st_size
                    stats["total_size_bytes"] += size

                    if size > stats["largest_file_size"]:
                        stats["largest_file_size"] = size
                        stats["largest_file"] = str(item.relative_to(self.memory_root))

                    # 统计文件类型
                    suffix = item.suffix.lower()
                    if suffix:
                        stats["file_types"][suffix] = stats["file_types"].get(suffix, 0) + 1
                    else:
                        stats["file_types"]["无扩展名"] = stats["file_types"].get("无扩展名", 0) + 1

                elif item.is_dir():
                    stats["total_directories"] += 1

            logger.debug(f"获取记忆统计信息: {stats}")
            return stats
        except Exception as e:
            logger.error(f"获取记忆统计信息失败: {e}")
            raise MemoryFileOperationError(f"无法获取记忆统计信息: {e}") from e

    def backup_memory(self, backup_path: str) -> None:
        """备份记忆数据

        Args:
            backup_path: 备份文件路径（.zip文件）

        Raises:
            MemoryFileOperationError: 备份失败
        """
        try:
            import zipfile

            backup_file = Path(backup_path)
            if not backup_file.suffix == '.zip':
                backup_file = backup_file.with_suffix('.zip')

            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if self.memory_root.exists():
                    for file_path in self.memory_root.rglob('*'):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            arcname = file_path.relative_to(self.memory_root)
                            zipf.write(file_path, arcname)

            logger.info(f"记忆数据已备份到: {backup_file}")
        except Exception as e:
            logger.error(f"备份记忆数据失败: {e}")
            raise MemoryFileOperationError(f"无法备份记忆数据到 {backup_path}: {e}") from e

    def restore_memory(self, backup_path: str) -> None:
        """从备份恢复记忆数据

        Args:
            backup_path: 备份文件路径

        Raises:
            MemoryFileOperationError: 恢复失败
        """
        try:
            import zipfile

            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise MemoryFileOperationError(f"备份文件不存在: {backup_path}")

            # 清除现有记忆
            self.clear_all_memory()

            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(self.memory_root)

            logger.info(f"记忆数据已从备份恢复: {backup_file}")
        except Exception as e:
            logger.error(f"恢复记忆数据失败: {e}")
            raise MemoryFileOperationError(f"无法从备份 {backup_path} 恢复记忆数据: {e}") from e
