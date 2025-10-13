#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Lake SDK 主客户端

提供了与 Anthropic Claude API 和记忆工具交互的主要接口。
"""

import os
import warnings
from typing import List, Dict, Any, Optional, Tuple, cast
from anthropic import Anthropic
from anthropic.types.beta import (
    BetaContextManagementConfigParam,
    BetaMessageParam,
)

from .memory_backend import BaseMemoryBackend, FileSystemMemoryBackend
from .exceptions import MemoryAPIError, MemoryBackendError
from .memory_tool import MemoryBackendTool

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


class MemoryLakeClient:
    """Memory Lake SDK 主客户端类

    提供了与 Anthropic Claude API 交互并处理记忆工具调用的完整功能。
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
        auto_save_memory: bool = True,
        use_full_schema: Optional[bool] = None,
        auto_handle_tool_calls: bool = False,
    ):
        """初始化 Memory Lake 客户端

        Args:
            api_key: Anthropic API 密钥，如果为 None 则从环境变量 ANTHROPIC_API_KEY 获取
            base_url: API 基础 URL，如果为 None 则从环境变量 ANTHHROPIC_BASE_URL 获取
            memory_backend: 记忆存储后端，如果为 None 则使用文件系统后端
            model: 要使用的 Claude 模型，如果为 None 则从环境变量 ANTHROPIC_MODEL 获取，
                  默认为 claude-4-sonnet
            max_tokens: 最大生成令牌数，默认为 2048
            context_management: 上下文管理配置，如果为 None 则使用默认配置
            memory_system_prompt: 记忆系统提示词，如果为 None 则使用默认提示词
            auto_save_memory: 是否自动保存记忆到持久化存储，默认为 True
            use_full_schema: (已弃用) 为兼容旧版本保留，不再对工具 schema 生效
            auto_handle_tool_calls: 是否自动处理工具调用并继续对话，默认为 False
        """
        # 从环境变量获取配置
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")
        model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

        if not api_key:
            raise ValueError("API 密钥未提供，请设置 api_key 参数或 ANTHROPIC_API_KEY 环境变量")

        # use_full_schema 参数在最新接口中已不再需要，保留以兼容旧调用
        if use_full_schema:
            warnings.warn(
                "use_full_schema 参数已弃用，SDK 将使用内置的 memory_20250818 schema。",
                RuntimeWarning,
            )
        self.use_full_schema = False

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
        self.auto_save_memory = auto_save_memory
        self.auto_handle_tool_calls = auto_handle_tool_calls
        self.history: List[BetaMessageParam] = []
        self.memory_tool = MemoryBackendTool(
            self.memory_backend,
            auto_save_callback=self._memory_tool_auto_save,
        )
        self._last_usage: Optional[Dict[str, Any]] = None

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
        self.history.append({"role": "user", "content": user_input})

        appended_events = 0

        try:
            events, text_reply = self._run_tool_runner()

            for event_type, payload in events:
                if event_type == "assistant":
                    self.history.append({"role": "assistant", "content": payload})
                elif event_type == "tool_result":
                    self.history.append({"role": "user", "content": payload})
                else:  # pragma: no cover - 防御性检查
                    continue
                appended_events += 1

            return text_reply

        except Exception as e:
            while appended_events > 0 and self.history:
                self.history.pop()
                appended_events -= 1
            if self.history:
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
            if self.auto_save_memory:
                self._auto_save_memory(path, "create", file_text=content)
        except Exception as e:
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
            return self.memory_backend.view(path, view_range)
        except Exception as e:
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
            if self.auto_save_memory:
                self._auto_save_memory(path, "delete")
        except Exception as e:
            raise MemoryBackendError(f"删除记忆失败: {e}") from e

    def clear_all_memories(self) -> None:
        """清除所有记忆

        Raises:
            MemoryBackendError: 记忆操作失败
        """
        try:
            self.memory_backend.clear_all_memory()
        except Exception as e:
            raise MemoryBackendError(f"清除所有记忆失败: {e}") from e

    def clear_conversation_history(self) -> None:
        """清除对话历史记录"""
        self.history.clear()

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

    def set_context_management(self, config: Dict[str, Any]) -> None:
        """设置上下文管理配置

        Args:
            config: 新的上下文管理配置
        """
        self.context_management = config

    def get_token_usage_info(self) -> Optional[Dict[str, Any]]:
        """获取最近一次API调用的令牌使用信息

        Returns:
            令牌使用信息字典，如果没有可用信息则返回 None
        """
        if self._last_usage is None:
            return None
        return dict(self._last_usage)

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
            raise MemoryBackendError(f"列出记忆失败: {e}") from e

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆存储统计信息

        Returns:
            包含统计信息的字典
        """
        try:
            return self.memory_backend.get_memory_stats()
        except Exception as e:
            raise MemoryBackendError(f"获取记忆统计信息失败: {e}") from e

    def backup_memory(self, backup_path: str) -> None:
        """备份记忆数据

        Args:
            backup_path: 备份文件路径
        """
        try:
            self.memory_backend.backup_memory(backup_path)
        except Exception as e:
            raise MemoryBackendError(f"备份记忆数据失败: {e}") from e

    def restore_memory(self, backup_path: str) -> None:
        """从备份恢复记忆数据

        Args:
            backup_path: 备份文件路径
        """
        try:
            self.memory_backend.restore_memory(backup_path)
        except Exception as e:
            raise MemoryBackendError(f"恢复记忆数据失败: {e}") from e

    def _run_tool_runner(self) -> Tuple[List[Tuple[str, Any]], str]:
        events: List[Tuple[str, Any]] = []
        text_parts: List[str] = []

        runner = self.client.beta.messages.tool_runner(
            betas=["context-management-2025-06-27"],
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=self.history,
            tools=[self.memory_tool],
            context_management=cast(BetaContextManagementConfigParam, self.context_management),
        )

        for message in runner:
            assistant_blocks: List[Dict[str, Any]] = []
            if hasattr(message, "usage") and message.usage:
                usage = message.usage
                if hasattr(usage, "model_dump"):
                    self._last_usage = usage.model_dump()
                else:  # pragma: no cover - 兼容旧版本 SDK
                    self._last_usage = dict(usage)  # type: ignore[arg-type]

            for content in message.content:
                if content.type == "text":
                    text_parts.append(content.text)
                    assistant_blocks.append({"type": "text", "text": content.text})
                elif content.type == "tool_use":
                    assistant_blocks.append(
                        {
                            "type": "tool_use",
                            "id": content.id,
                            "name": content.name,
                            "input": content.input,
                        }
                    )

            if assistant_blocks:
                events.append(("assistant", assistant_blocks))

            tool_response = runner.generate_tool_call_response()
            if tool_response and tool_response.get("content"):
                events.append(("tool_result", tool_response["content"]))

        return events, "".join(text_parts)

    def _auto_save_memory(self, path: str, operation: str, **kwargs) -> None:
        """自动保存记忆到持久化存储

        Args:
            path: 记忆文件路径
            operation: 操作类型 (create, str_replace, insert, delete, rename)
            **kwargs: 操作相关的额外参数
        """
        if not self.auto_save_memory:
            return

        # 对于文件系统后端，记忆操作已直接写入文件系统
        # 此方法可以用于：
        # 1. 记录操作日志
        # 2. 触发备份操作
        # 3. 同步到其他存储后端
        # 4. 验证操作结果

        # 验证操作是否成功
        if operation in ["create", "str_replace", "insert"] and hasattr(self.memory_backend, 'memory_exists'):
            if not self.memory_backend.memory_exists(path):
                raise MemoryBackendError(f"自动保存验证失败: 文件 {path} 未找到")

    def _memory_tool_auto_save(self, path: str, operation: str, extra: Dict[str, Any]) -> None:
        if not self.auto_save_memory:
            return
        self._auto_save_memory(path, operation, **extra)

    def interactive_loop(self):
        """启动交互式对话循环"""
        print("Memory Lake SDK - 交互式对话")
        print("命令: /quit, /clear, /memory_view, /memory_clear, /history, /autosave, /help")

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
                    print("\n记忆内容:")
                    print(result)
                except Exception as e:
                    print(f"获取记忆失败: {e}")
                continue
            elif user_input.lower() == "/memory_clear":
                try:
                    self.clear_all_memories()
                    print("所有记忆已清除")
                except Exception as e:
                    print(f"清除记忆失败: {e}")
                continue
            elif user_input.lower() == "/history":
                history = self.get_conversation_history()
                print(f"\n对话历史 (共 {len(history)} 条):")
                for i, msg in enumerate(history):
                    role = msg["role"].upper()
                    content = msg["content"]
                    if isinstance(content, str):
                        print(f"[{i+1}] {role}: {content[:100]}...")
                    else:
                        print(f"[{i+1}] {role}: [复杂内容]")
                continue
            elif user_input.lower() == "/autosave":
                self.auto_save_memory = not self.auto_save_memory
                print(f"自动保存: {'已启用' if self.auto_save_memory else '已禁用'}")
                continue
            elif user_input.lower() == "/help":
                print("\n帮助:")
                print("- 直接输入消息与 Claude 对话")
                print("- Memory Lake 会自动管理记忆")
                print(f"- 自动保存: {'已启用' if self.auto_save_memory else '已禁用'}")
                continue
            elif not user_input:
                continue

            try:
                print("\nClaude: ", end="", flush=True)
                response = self.chat(user_input)
                print(response)
            except Exception as e:
                print(f"\n对话失败: {e}")
