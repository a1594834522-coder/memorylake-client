"""
Claude Memory SDK 记忆操作模块
"""

import os
import json
import re
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from .models import MemoryViewResponse, MemoryCreateRequest, MemoryResponse
from .exceptions import MemoryError, ValidationError


class MemoryOperations:
    """记忆操作高级接口"""

    def __init__(self, client):
        """初始化记忆操作

        Args:
            client: ClaudeMemoryClient实例
        """
        self.client = client

    def create_memory(self, path: str, content: str, overwrite: bool = False) -> MemoryResponse:
        """
        创建记忆文件

        Args:
            path: 文件路径
            content: 文件内容
            overwrite: 是否覆盖已存在的文件

        Returns:
            操作响应
        """
        if not path.startswith("/memories"):
            raise ValidationError("Path must start with /memories")

        # 检查文件是否已存在
        if not overwrite:
            try:
                existing = self.client.view_memory(path)
                raise MemoryError(f"File {path} already exists. Use overwrite=True to replace it.")
            except Exception:
                pass  # 文件不存在，可以继续

        return self.client.create_memory_file(path, content)

    def update_memory(self, path: str, content: str, create_if_not_exists: bool = False) -> MemoryResponse:
        """
        更新记忆文件

        Args:
            path: 文件路径
            content: 新的文件内容
            create_if_not_exists: 如果文件不存在是否创建

        Returns:
            操作响应
        """
        if not path.startswith("/memories"):
            raise ValidationError("Path must start with /memories")

        try:
            # 尝试读取现有文件
            self.client.view_memory(path)
            return self.client.create_memory_file(path, content)
        except Exception:
            if create_if_not_exists:
                return self.client.create_memory_file(path, content)
            else:
                raise MemoryError(f"File {path} does not exist")

    def append_memory(self, path: str, content: str, separator: str = "\n\n") -> MemoryResponse:
        """
        追加内容到记忆文件

        Args:
            path: 文件路径
            content: 要添加的内容
            separator: 分隔符

        Returns:
            操作响应
        """
        if not path.startswith("/memories"):
            raise ValidationError("Path must start with /memories")

        try:
            # 读取现有内容
            existing_response = self.client.view_memory(path)
            existing_content = existing_response.contents

            # 添加新内容
            new_content = existing_content + separator + content
            return self.client.create_memory_file(path, new_content)
        except Exception as e:
            raise MemoryError(f"Failed to append to {path}: {str(e)}")

    def delete_memory(self, path: str) -> MemoryResponse:
        """
        删除记忆文件或目录

        Args:
            path: 文件或目录路径

        Returns:
            操作响应
        """
        return self.client.delete_memory_file(path)

    def search_memories(self, keyword: str, path: str = "/memories") -> List[Dict[str, Any]]:
        """
        搜索记忆内容

        Args:
            keyword: 搜索关键词
            path: 搜索路径

        Returns:
            搜索结果列表
        """
        results = []

        try:
            # 获取文件列表
            files_response = self.client.list_memory_files()

            for file_info in files_response.files:
                file_path = f"{path.rstrip('/')}/{file_info.name}"

                try:
                    # 读取文件内容
                    content_response = self.client.view_memory(file_path)
                    content = content_response.contents

                    # 搜索关键词
                    if keyword.lower() in content.lower():
                        # 提取匹配的行
                        matching_lines = []
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if keyword.lower() in line.lower():
                                matching_lines.append({
                                    'line_number': i,
                                    'content': line.strip()
                                })

                        results.append({
                            'file': file_info.name,
                            'path': file_path,
                            'matches': len(matching_lines),
                            'lines': matching_lines
                        })

                except Exception:
                    # 忽略无法读取的文件
                    continue

        except Exception as e:
            raise MemoryError(f"Failed to search memories: {str(e)}")

        return results

    def get_memory_summary(self, path: str = "/memories") -> Dict[str, Any]:
        """
        获取记忆摘要信息

        Args:
            path: 记忆路径

        Returns:
            摘要信息字典
        """
        summary = {
            'path': path,
            'files': [],
            'total_files': 0,
            'total_size': 0,
            'last_modified': None
        }

        try:
            files_response = self.client.list_memory_files()
            summary['total_files'] = len(files_response.files)

            for file_info in files_response.files:
                summary['files'].append({
                    'name': file_info.name,
                    'path': f"{path.rstrip('/')}/{file_info.name}",
                    'size': file_info.size
                })
                summary['total_size'] += file_info.size or 0

            summary['generated_at'] = datetime.now().isoformat()

        except Exception as e:
            raise MemoryError(f"Failed to get memory summary: {str(e)}")

        return summary

    def backup_memory(self, backup_path: str, paths: Optional[List[str]] = None) -> str:
        """
        备份记忆文件

        Args:
            backup_path: 备份文件路径
            paths: 要备份的路径列表，None表示备份所有

        Returns:
            备份文件路径
        """
        if paths is None:
            # 备份所有文件
            backup_data = self.client.export_memory("json")
        else:
            # 备份指定路径
            backup_data = {}
            for path in paths:
                try:
                    if path.endswith('/'):
                        # 目录
                        dir_files = self.client.list_memory_files()
                        backup_data[path] = {
                            'type': 'directory',
                            'files': []
                        }

                        for file_info in dir_files.files:
                            file_path = f"{path.rstrip('/')}/{file_info.name}"
                            content_response = self.client.view_memory(file_path)
                            backup_data[path]['files'].append({
                                'name': file_info.name,
                                'content': content_response.contents
                            })
                    else:
                        # 文件
                        content_response = self.client.view_memory(path)
                        backup_data[path] = {
                            'type': 'file',
                            'content': content_response.contents
                        }
                except Exception as e:
                    backup_data[path] = {'error': str(e)}

        # 写入备份文件
        backup_file = Path(backup_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)

        backup_content = json.dumps({
            'backup_timestamp': datetime.now().isoformat(),
            'memory_data': backup_data,
            'version': '1.0'
        }, indent=2, ensure_ascii=False)

        backup_file.write_text(backup_content, encoding='utf-8')
        return str(backup_file.absolute())

    def restore_memory(self, backup_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        从备份恢复记忆

        Args:
            backup_path: 备份文件路径
            overwrite: 是否覆盖现有文件

        Returns:
            恢复结果统计
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise MemoryError(f"Backup file not found: {backup_path}")

        try:
            backup_data = json.loads(backup_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            raise MemoryError(f"Invalid backup file format: {e}")

        memory_data = backup_data.get('memory_data', {})
        results = {
            'restored': 0,
            'failed': 0,
            'errors': []
        }

        for path, data in memory_data.items():
            try:
                if data.get('type') == 'directory':
                    # 处理目录
                    files = data.get('files', [])
                    for file_data in files:
                        file_path = f"{path.rstrip('/')}/{file_data['name']}"
                        if isinstance(file_data.get('content'), str):
                            self.create_memory(file_path, file_data['content'], overwrite)
                            results['restored'] += 1

                elif data.get('type') == 'file':
                    # 处理文件
                    if isinstance(data.get('content'), str):
                        self.create_memory(path, data['content'], overwrite)
                        results['restored'] += 1

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{path}: {str(e)}")

        return results

    def organize_memories(self, rules: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        整理记忆文件

        Args:
            rules: 组织规则，{pattern: target_path}

        Returns:
            整理结果
        """
        if rules is None:
            # 默认组织规则
            rules = {
                r'.*profile.*': '/memories/profiles/',
                r'.*preference.*': '/memories/preferences/',
                r'.*project.*': '/memories/projects/',
                r'.*note.*': '/memories/notes/',
                r'.*todo.*': '/memories/tasks/',
                r'.*idea.*': '/memories/ideas/'
            }

        results = {
            'moved': 0,
            'failed': 0,
            'errors': []
        }

        try:
            files_response = self.client.list_memory_files()

            for file_info in files_response.files:
                file_path = f"/memories/{file_info.name}"

                # 检查是否匹配任何规则
                for pattern, target_path in rules.items():
                    if re.match(pattern, file_info.name, re.IGNORECASE):
                        try:
                            # 读取文件内容
                            content_response = self.client.view_memory(file_path)
                            content = content_response.contents

                            # 创建目标目录
                            target_file = f"{target_path.rstrip('/')}/{file_info.name}"

                            # 创建文件
                            self.create_memory(target_file, content, overwrite=True)

                            # 删除原文件
                            self.delete_memory(file_path)

                            results['moved'] += 1
                            break

                        except Exception as e:
                            results['failed'] += 1
                            results['errors'].append(f"{file_info.name}: {str(e)}")

        except Exception as e:
            raise MemoryError(f"Failed to organize memories: {str(e)}")

        return results

    def cleanup_old_memories(self, days: int = 30) -> Dict[str, Any]:
        """
        清理旧的记忆文件

        Args:
            days: 天数阈值

        Returns:
            清理结果
        """
        results = {
            'deleted': 0,
            'failed': 0,
            'errors': []
        }

        # 这里需要扩展服务端API来支持文件时间戳
        # 目前只是示例实现
        try:
            files_response = self.client.list_memory_files()

            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

            for file_info in files_response.files:
                file_path = f"/memories/{file_info.name}"

                try:
                    # 尝试获取文件信息（需要扩展API）
                    # 这里可以添加文件时间戳检查逻辑

                    # 简单实现：删除超过天数的文件
                    # 实际实现需要服务端支持文件元数据
                    pass

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{file_info.name}: {str(e)}")

        except Exception as e:
            raise MemoryError(f"Failed to cleanup old memories: {str(e)}")

        return results