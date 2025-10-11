#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Memory SDK 主客户端

提供了与 Claude API 和记忆工具交互的主要接口。
"""

import logging
import os
from typing import List, Dict, Any, Optional, cast
from anthropic import Anthropic
from anthropic.types.beta import (
    BetaMessage,
    BetaMessageParam,
    BetaContentBlockParam,
    BetaToolParam,
    BetaContextManagementConfigParam,
    BetaMemoryTool20250818Param,
    BetaMemoryTool20250818Command,
    BetaMemoryTool20250818ViewCommand,
    BetaMemoryTool20250818CreateCommand,
    BetaMemoryTool20250818DeleteCommand,
    BetaMemoryTool20250818InsertCommand,
    BetaMemoryTool20250818RenameCommand,
    BetaMemoryTool20250818StrReplaceCommand,
)

from .memory_backend import BaseMemoryBackend, FileSystemMemoryBackend
from .exceptions import MemoryAPIError, MemoryBackendError

# 设置日志
logger = logging.getLogger(__name__)

# 默认记忆系统提示词
MEMORY_SYSTEM_PROMPT = """- ***DO NOT just store the conversation history**
- No need to mention your memory tool or what you are writting in it to the user, unless they ask
- Store facts about the user and their preferences
- Before responding, check memory to adjust technical depth and response style appropriately
- Keep memories up-to-date - remove outdated info, add new details as you learn them
- Use an xml format like <xml><name>John Doe</name></user></xml>"""

# 默认上下文管理配置
DEFAULT_CONTEXT_MANAGEMENT = {
    "edits": [
        {
            "type": "clear_tool_uses_20250919",
            "trigger": {"type": "input_tokens", "value": 30000},
            "keep": {"type": "tool_uses", "value": 3},
            "clear_at_least": {"type": "input_tokens", "value": 5000},
            "exclude_tools": ["memory"],
        }
    ]
}


class ClaudeMemoryClient:
    """Claude Memory SDK 主客户端类

    提供了与 Claude API 交互并处理记忆工具调用的完整功能。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        memory_backend: Optional[BaseMemoryBackend] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        context_management: Optional[Dict[str, Any]] = None,
        memory_system_prompt: Optional[str] = None,
    ):
        """初始化 Claude Memory 客户端

        Args:
            api_key: Anthropic API 密钥，如果为 None 则从环境变量 ANTHROPIC_API_KEY 获取
            base_url: API 基础 URL，如果为 None 则从环境变量 ANTHHROPIC_BASE_URL 获取
            memory_backend: 记忆存储后端，如果为 None 则使用文件系统后端
            model: 要使用的 Claude 模型，如果为 None 则从环境变量 ANTHROPIC_MODEL 获取，
                  默认为 claude-4-sonnet
            max_tokens: 最大生成令牌数，默认为 2048
            context_management: 上下文管理配置，如果为 None 则使用默认配置
            memory_system_prompt: 记忆系统提示词，如果为 None 则使用默认提示词
        """
        # 从环境变量获取配置
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")
        model = model or os.getenv("ANTHROPIC_MODEL", "claude-4-sonnet")

        if not api_key:
            raise ValueError("API 密钥未提供，请设置 api_key 参数或 ANTHROPIC_API_KEY 环境变量")

        # 初始化 Anthropic 客户端
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = Anthropic(**client_kwargs)
        self.memory_backend = memory_backend or FileSystemMemoryBackend()
        self.model = model
        self.max_tokens = max_tokens
        self.context_management = context_management or DEFAULT_CONTEXT_MANAGEMENT
        self.system_prompt = memory_system_prompt or MEMORY_SYSTEM_PROMPT
        self.history: List[BetaMessageParam] = []

        logger.info(f"Claude Memory 客户端初始化完成，模型: {model}")
        if base_url:
            logger.info(f"使用自定义 API 基础 URL: {base_url}")

    def chat(self, user_input: str) -> str:
        """发送消息并获得回复

        Args:
            user_input: 用户输入的消息

        Returns:
            Claude 的回复文本

        Raises:
            MemoryAPIError: API 调用失败
            MemoryBackendError: 记忆后端操作失败
        """
        # 添加用户输入到历史记录
        self.history.append({"role": "user", "content": user_input})
        logger.debug(f"添加用户消息: {user_input[:50]}...")

        try:
            response = self._create_message()
            assistant_response = self._process_response(response)

            # 添加助手回复到历史记录
            self.history.append({"role": "assistant", "content": assistant_response})

            # 提取并返回纯文本回复
            return self._extract_text_from_response(assistant_response)

        except Exception as e:
            logger.error(f"聊天过程中发生错误: {e}")
            # 从历史记录中移除失败的用户输入
            self.history.pop()
            raise MemoryAPIError(f"聊天失败: {e}") from e

    
    def add_memory(self, path: str, content: str) -> None:
        """添加记忆

        Args:
            path: 记忆文件路径，必须以 '/memories' 开头
            content: 记忆内容

        Raises:
            MemoryBackendError: 记忆操作失败
        """
        try:
            self.memory_backend.create(path, content)
            logger.info(f"添加记忆: {path}")
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            raise MemoryBackendError(f"添加记忆失败: {e}") from e

    def get_memory(self, path: str, view_range: Optional[tuple] = None) -> str:
        """获取记忆

        Args:
            path: 记忆文件或目录路径，必须以 '/memories' 开头
            view_range: 可选的行范围 (start_line, end_line)

        Returns:
            记忆内容

        Raises:
            MemoryBackendError: 记忆操作失败
        """
        try:
            result = self.memory_backend.view(path, view_range)
            logger.debug(f"获取记忆: {path}")
            return result
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            raise MemoryBackendError(f"获取记忆失败: {e}") from e

    def delete_memory(self, path: str) -> None:
        """删除记忆

        Args:
            path: 要删除的记忆路径，必须以 '/memories' 开头

        Raises:
            MemoryBackendError: 记忆操作失败
        """
        try:
            self.memory_backend.delete(path)
            logger.info(f"删除记忆: {path}")
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            raise MemoryBackendError(f"删除记忆失败: {e}") from e

    def clear_all_memories(self) -> None:
        """清除所有记忆

        Raises:
            MemoryBackendError: 记忆操作失败
        """
        try:
            self.memory_backend.clear_all_memory()
            logger.info("已清除所有记忆")
        except Exception as e:
            logger.error(f"清除所有记忆失败: {e}")
            raise MemoryBackendError(f"清除所有记忆失败: {e}") from e

    def clear_conversation_history(self) -> None:
        """清除对话历史记录"""
        self.history.clear()
        logger.info("已清除对话历史记录")

    def get_conversation_history(self) -> List[BetaMessageParam]:
        """获取对话历史记录

        Returns:
            对话历史记录列表
        """
        return self.history.copy()

    def set_system_prompt(self, prompt: str) -> None:
        """设置系统提示

        Args:
            prompt: 新的系统提示
        """
        self.system_prompt = prompt
        logger.info("系统提示已更新")

    def set_context_management(self, config: Dict[str, Any]) -> None:
        """设置上下文管理配置

        Args:
            config: 新的上下文管理配置
        """
        self.context_management = config
        logger.info("上下文管理配置已更新")

    def get_token_usage_info(self) -> Optional[Dict[str, Any]]:
        """获取最近一次API调用的令牌使用信息

        Returns:
            令牌使用信息字典，如果没有可用信息则返回 None
        """
        # 这里需要从最近的响应中提取使用信息
        # 实际实现需要存储最近的响应对象
        logger.debug("令牌使用信息功能待实现")
        return None

    def memory_exists(self, path: str) -> bool:
        """检查记忆是否存在

        Args:
            path: 记忆文件或目录路径，必须以 '/memories' 开头

        Returns:
            如果记忆存在则返回 True，否则返回 False
        """
        try:
            return self.memory_backend.memory_exists(path)
        except Exception as e:
            logger.error(f"检查记忆存在性失败: {e}")
            raise MemoryBackendError(f"检查记忆存在性失败: {e}") from e

    def list_memories(self, path: str = "/memories") -> List[str]:
        """列出指定目录下的所有记忆

        Args:
            path: 目录路径，必须以 '/memories' 开头，默认为根目录

        Returns:
            记忆文件和目录的路径列表
        """
        try:
            return self.memory_backend.list_memories(path)
        except Exception as e:
            logger.error(f"列出记忆失败: {e}")
            raise MemoryBackendError(f"列出记忆失败: {e}") from e

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆存储统计信息

        Returns:
            包含统计信息的字典
        """
        try:
            return self.memory_backend.get_memory_stats()
        except Exception as e:
            logger.error(f"获取记忆统计信息失败: {e}")
            raise MemoryBackendError(f"获取记忆统计信息失败: {e}") from e

    def backup_memory(self, backup_path: str) -> None:
        """备份记忆数据

        Args:
            backup_path: 备份文件路径
        """
        try:
            self.memory_backend.backup_memory(backup_path)
            logger.info(f"记忆数据已备份到: {backup_path}")
        except Exception as e:
            logger.error(f"备份记忆数据失败: {e}")
            raise MemoryBackendError(f"备份记忆数据失败: {e}") from e

    def restore_memory(self, backup_path: str) -> None:
        """从备份恢复记忆数据

        Args:
            backup_path: 备份文件路径
        """
        try:
            self.memory_backend.restore_memory(backup_path)
            logger.info(f"记忆数据已从备份恢复: {backup_path}")
        except Exception as e:
            logger.error(f"恢复记忆数据失败: {e}")
            raise MemoryBackendError(f"恢复记忆数据失败: {e}") from e

    def _create_message(self) -> BetaMessage:
        """创建 API 消息请求"""
        try:
            # 完整的 memory tool 定义，包含 input_schema
            memory_tool = {
                "type": "memory_20250818",
                "name": "memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "enum": ["view", "create", "str_replace", "insert", "delete", "rename"],
                            "description": "要执行的命令类型"
                        },
                        "path": {
                            "type": "string",
                            "description": "文件或目录路径，必须以 /memories 开头"
                        },
                        "view_range": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                            "description": "可选的行范围 [start_line, end_line]，仅用于 view 命令"
                        },
                        "file_text": {
                            "type": "string",
                            "description": "文件内容，用于 create 命令"
                        },
                        "old_str": {
                            "type": "string",
                            "description": "要替换的旧文本，用于 str_replace 命令"
                        },
                        "new_str": {
                            "type": "string",
                            "description": "新文本，用于 str_replace 命令"
                        },
                        "insert_line": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "插入行号，用于 insert 命令"
                        },
                        "insert_text": {
                            "type": "string",
                            "description": "要插入的文本，用于 insert 命令"
                        },
                        "old_path": {
                            "type": "string",
                            "description": "原路径，用于 rename 命令"
                        },
                        "new_path": {
                            "type": "string",
                            "description": "新路径，用于 rename 命令"
                        }
                    },
                    "required": ["command", "path"],
                    "allOf": [
                        {
                            "if": {"properties": {"command": {"const": "view"}}},
                            "then": {"required": ["command", "path"]},
                            "else": True
                        },
                        {
                            "if": {"properties": {"command": {"const": "create"}}},
                            "then": {"required": ["command", "path", "file_text"]},
                            "else": True
                        },
                        {
                            "if": {"properties": {"command": {"const": "str_replace"}}},
                            "then": {"required": ["command", "path", "old_str", "new_str"]},
                            "else": True
                        },
                        {
                            "if": {"properties": {"command": {"const": "insert"}}},
                            "then": {"required": ["command", "path", "insert_line", "insert_text"]},
                            "else": True
                        },
                        {
                            "if": {"properties": {"command": {"const": "delete"}}},
                            "then": {"required": ["command", "path"]},
                            "else": True
                        },
                        {
                            "if": {"properties": {"command": {"const": "rename"}}},
                            "then": {"required": ["command", "old_path", "new_path"]},
                            "else": True
                        }
                    ]
                }
            }

            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=self.history,
                tools=[memory_tool],
                betas=["context-management-2025-06-27"],
                system=self.system_prompt,
                context_management=cast(BetaContextManagementConfigParam, self.context_management),
            )
            return response
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            raise MemoryAPIError(f"API 调用失败: {e}") from e

    def _process_response(self, response: BetaMessage) -> List[Dict[str, Any]]:
        """处理 API 响应，处理工具调用

        Args:
            response: API 响应

        Returns:
            处理后的助手消息内容
        """
        assistant_content: List[Dict[str, Any]] = []
        tool_results_needed = False

        # 检查上下文管理操作
        if hasattr(response, 'context_management') and response.context_management:
            for edit in response.context_management.applied_edits:
                logger.info(f"上下文管理操作: {edit.type}")

        # 处理响应内容块
        for content_block in response.content:
            if content_block.type == "text":
                assistant_content.append({
                    "type": "text",
                    "text": content_block.text
                })

            elif content_block.type == "tool_use" and content_block.name == "memory":
                # 处理记忆工具调用
                tool_input = content_block.input
                logger.debug(f"记忆工具调用: {tool_input.get('command')}")

                assistant_content.append({
                    "type": "tool_use",
                    "id": content_block.id,
                    "name": content_block.name,
                    "input": tool_input,
                })

                tool_results_needed = True

        # 如果需要工具结果，继续处理
        if tool_results_needed:
            return self._handle_tool_calls(assistant_content)

        return assistant_content

    def _handle_tool_calls(self, assistant_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理工具调用并获取结果

        Args:
            assistant_content: 助手内容，包含工具调用

        Returns:
            完整的助手响应内容
        """
        tool_results = []

        for content_block in assistant_content:
            if content_block.get("type") == "tool_use" and content_block.get("name") == "memory":
                tool_id = content_block["id"]
                tool_input = content_block["input"]

                try:
                    result = self._handle_memory_tool(tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result
                    })
                except Exception as e:
                    logger.error(f"工具调用失败: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": f"错误: {e}",
                        "is_error": True
                    })

        # 如果有工具结果，添加到历史记录并继续对话
        if tool_results:
            self.history.append({"role": "user", "content": tool_results})

            # 继续获取最终响应
            try:
                response = self._create_message()
                final_content = self._process_response(response)
                assistant_content.extend(final_content)
            except Exception as e:
                logger.error(f"获取最终响应失败: {e}")
                raise MemoryAPIError(f"获取最终响应失败: {e}") from e

        return assistant_content

    def _handle_memory_tool(self, tool_input: Dict[str, Any]) -> str:
        """处理记忆工具调用

        Args:
            tool_input: 工具输入参数

        Returns:
            工具执行结果
        """
        command = tool_input.get("command")

        try:
            if command == "view":
                path = tool_input["path"]
                view_range = tool_input.get("view_range")
                return self.memory_backend.view(path, view_range)

            elif command == "create":
                path = tool_input["path"]
                file_text = tool_input["file_text"]
                self.memory_backend.create(path, file_text)
                return f"文件 {path} 创建成功"

            elif command == "str_replace":
                path = tool_input["path"]
                old_str = tool_input["old_str"]
                new_str = tool_input["new_str"]
                self.memory_backend.str_replace(path, old_str, new_str)
                return f"文件 {path} 已更新"

            elif command == "insert":
                path = tool_input["path"]
                insert_line = tool_input["insert_line"]
                insert_text = tool_input["insert_text"]
                self.memory_backend.insert(path, insert_line, insert_text)
                return f"已在文件 {path} 的第 {insert_line} 行插入内容"

            elif command == "delete":
                path = tool_input["path"]
                self.memory_backend.delete(path)
                return f"已删除 {path}"

            elif command == "rename":
                old_path = tool_input["old_path"]
                new_path = tool_input["new_path"]
                self.memory_backend.rename(old_path, new_path)
                return f"已将 {old_path} 重命名为 {new_path}"

            else:
                return f"不支持的命令: {command}"

        except Exception as e:
            logger.error(f"记忆工具操作失败: {e}")
            return f"操作失败: {e}"

    @staticmethod
    def _extract_text_from_response(assistant_content: List[Dict[str, Any]]) -> str:
        """从助手响应中提取纯文本

        Args:
            assistant_content: 助手响应内容

        Returns:
            纯文本回复
        """
        text_parts = []
        for content_block in assistant_content:
            if content_block.get("type") == "text":
                text_parts.append(content_block["text"])
        return "".join(text_parts)

    def interactive_loop(self):
        """启动交互式对话循环"""
        print("Claude Memory SDK - 交互式对话")
        print("命令:")
        print("  /quit 或 /exit - 退出会话")
        print("  /clear - 开始新的对话")
        print("  /memory_view - 查看所有记忆文件")
        print("  /memory_clear - 删除所有记忆")
        print("  /history - 查看对话历史")
        print("  /help - 显示帮助信息")

        while True:
            try:
                user_input = input("\n您: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见!")
                break

            if user_input.lower() in ["/quit", "/exit"]:
                print("再见!")
                break
            elif user_input.lower() == "/clear":
                self.clear_conversation_history()
                print("对话已清除!")
                continue
            elif user_input.lower() == "/memory_view":
                try:
                    result = self.get_memory("/memories")
                    print("\n[记忆内容]:")
                    print(result)
                except Exception as e:
                    print(f"[ERROR] 获取记忆失败: {e}")
                continue
            elif user_input.lower() == "/memory_clear":
                try:
                    self.clear_all_memories()
                    print("[OK] 所有记忆已清除")
                except Exception as e:
                    print(f"[ERROR] 清除记忆失败: {e}")
                continue
            elif user_input.lower() == "/history":
                history = self.get_conversation_history()
                print(f"\n[对话历史] (共 {len(history)} 条):")
                for i, msg in enumerate(history):
                    role = msg["role"].upper()
                    content = msg["content"]
                    if isinstance(content, str):
                        print(f"[{i+1}] {role}: {content[:100]}...")
                    else:
                        print(f"[{i+1}] {role}: [复杂内容]")
                continue
            elif user_input.lower() == "/help":
                print("\n[帮助信息]:")
                print("- 直接输入消息与Claude对话")
                print("- Claude会自动管理记忆，存储重要信息")
                print("- 使用 /memory_view 查看Claude记住的内容")
                continue
            elif not user_input:
                continue

            try:
                print("\nClaude: ", end="", flush=True)
                response = self.chat(user_input)
                print(response)
            except Exception as e:
                print(f"\n[ERROR] 对话失败: {e}")