"""
Claude Memory SDK 对话管理模块
"""

import uuid
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

from .models import QuestionRequest, QuestionResponse
from .exceptions import SessionError


@dataclass
class Message:
    """对话消息"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """对话会话"""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_files: List[str] = field(default_factory=list)

    def add_message(self, role: str, content: str, **metadata) -> Message:
        """添加消息到对话"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata
        )
        self.messages.append(message)
        self.last_activity = datetime.now()
        return message

    def get_last_message(self, role: Optional[str] = None) -> Optional[Message]:
        """获取最后一条消息"""
        if not self.messages:
            return None

        if role is None:
            return self.messages[-1]

        for message in reversed(self.messages):
            if message.role == role:
                return message
        return None

    def get_recent_messages(self, count: int = 10, role: Optional[str] = None) -> List[Message]:
        """获取最近的消息"""
        if role is None:
            return self.messages[-count:] if self.messages else []

        filtered = [msg for msg in self.messages if msg.role == role]
        return filtered[-count:] if filtered else []

    def to_api_format(self) -> List[Dict[str, str]]:
        """转换为API格式"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]


class ConversationManager:
    """对话管理器"""

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.current_conversation_id: Optional[str] = None

    def create_conversation(self, title: Optional[str] = None) -> str:
        """创建新对话"""
        conversation = Conversation(title=title)
        self.conversations[conversation.conversation_id] = conversation
        self.current_conversation_id = conversation.conversation_id
        return conversation.conversation_id

    def get_conversation(self, conversation_id: str) -> Conversation:
        """获取对话"""
        if conversation_id not in self.conversations:
            raise SessionError(f"Conversation {conversation_id} not found")
        return self.conversations[conversation_id]

    def get_current_conversation(self) -> Conversation:
        """获取当前对话"""
        if not self.current_conversation_id:
            return self.create_conversation()
        return self.get_conversation(self.current_conversation_id)

    def switch_conversation(self, conversation_id: str) -> Conversation:
        """切换对话"""
        conversation = self.get_conversation(conversation_id)
        self.current_conversation_id = conversation_id
        return conversation

    def delete_conversation(self, conversation_id: str) -> None:
        """删除对话"""
        if conversation_id not in self.conversations:
            raise SessionError(f"Conversation {conversation_id} not found")

        del self.conversations[conversation_id]

        if self.current_conversation_id == conversation_id:
            self.current_conversation_id = None

    def list_conversations(self) -> List[Conversation]:
        """列出所有对话"""
        return sorted(
            self.conversations.values(),
            key=lambda conv: conv.last_activity,
            reverse=True
        )

    def clear_conversations(self) -> None:
        """清除所有对话"""
        self.conversations.clear()
        self.current_conversation_id = None

    def add_message_to_current(self, role: str, content: str, **metadata) -> Message:
        """向当前对话添加消息"""
        conversation = self.get_current_conversation()
        return conversation.add_message(role, content, **metadata)

    def get_conversation_stats(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        total_messages = sum(len(conv.messages) for conv in self.conversations.values())
        return {
            "total_conversations": len(self.conversations),
            "total_messages": total_messages,
            "current_conversation_id": self.current_conversation_id,
            "active_conversations": len([
                conv for conv in self.conversations.values()
                if (datetime.now() - conv.last_activity).days < 7
            ])
        }