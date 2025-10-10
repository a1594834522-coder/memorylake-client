"""
会话管理器 - 统一管理服务端会话状态
"""

import time
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from anthropic.types import MessageParam


@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    messages: List[MessageParam]


class SessionManager:
    """
    统一的会话管理器

    负责管理所有会话状态，包括创建、获取、清理和会话过期处理
    """

    def __init__(self, session_timeout_minutes: int = 60, max_sessions: int = 1000):
        """
        初始化会话管理器

        Args:
            session_timeout_minutes: 会话超时时间（分钟）
            max_sessions: 最大会话数量
        """
        self.sessions: Dict[str, SessionInfo] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_sessions = max_sessions

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        创建新会话

        Args:
            session_id: 可选的会话ID，如果为None则自动生成

        Returns:
            会话ID
        """
        # 清理过期会话
        self._cleanup_expired_sessions()

        # 检查会话数量限制
        if len(self.sessions) >= self.max_sessions:
            self._remove_oldest_sessions()

        # 生成或使用提供的会话ID
        if session_id is None or session_id in self.sessions:
            session_id = f"session_{int(time.time())}_{os.urandom(4).hex()}"

        now = datetime.now()
        self.sessions[session_id] = SessionInfo(
            session_id=session_id,
            created_at=now,
            last_activity=now,
            message_count=0,
            messages=[]
        )

        return session_id

    def get_session(self, session_id: Optional[str]) -> str:
        """
        获取或创建会话

        Args:
            session_id: 会话ID，如果为None或不存在则创建新会话

        Returns:
            有效的会话ID
        """
        if session_id is None or session_id not in self.sessions:
            return self.create_session(session_id)

        # 更新最后活动时间
        self.sessions[session_id].last_activity = datetime.now()
        return session_id

    def get_session_messages(self, session_id: str) -> List[MessageParam]:
        """
        获取会话消息

        Args:
            session_id: 会话ID

        Returns:
            消息列表

        Raises:
            KeyError: 会话不存在
        """
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")

        self.sessions[session_id].last_activity = datetime.now()
        return self.sessions[session_id].messages

    def add_message_to_session(self, session_id: str, message: MessageParam) -> None:
        """
        向会话添加消息

        Args:
            session_id: 会话ID
            message: 消息内容

        Raises:
            KeyError: 会话不存在
        """
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")

        session_info = self.sessions[session_id]
        session_info.messages.append(message)
        session_info.message_count += 1
        session_info.last_activity = datetime.now()

    def clear_session(self, session_id: str) -> bool:
        """
        清除会话历史

        Args:
            session_id: 会话ID

        Returns:
            是否成功清除
        """
        if session_id not in self.sessions:
            return False

        session_info = self.sessions[session_id]
        session_info.messages = []
        session_info.message_count = 0
        session_info.last_activity = datetime.now()

        return True

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功删除
        """
        if session_id not in self.sessions:
            return False

        del self.sessions[session_id]
        return True

    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """
        获取会话详细信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息，如果不存在则返回None
        """
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[str]:
        """
        列出所有活跃会话ID

        Returns:
            会话ID列表
        """
        self._cleanup_expired_sessions()
        return list(self.sessions.keys())

    def get_stats(self) -> Dict:
        """
        获取会话统计信息

        Returns:
            统计信息字典
        """
        self._cleanup_expired_sessions()

        total_messages = sum(session.message_count for session in self.sessions.values())

        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / max(len(self.sessions), 1),
            "oldest_session": min((s.created_at for s in self.sessions.values()), default=None),
            "newest_session": max((s.created_at for s in self.sessions.values()), default=None)
        }

    def _cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, session_info in self.sessions.items()
            if now - session_info.last_activity > self.session_timeout
        ]

        for session_id in expired_sessions:
            del self.sessions[session_id]

    def _remove_oldest_sessions(self, count: int = 10) -> None:
        """移除最旧的会话以释放空间"""
        if len(self.sessions) <= count:
            self.sessions.clear()
            return

        # 按最后活动时间排序，移除最旧的
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1].last_activity
        )

        for session_id, _ in sorted_sessions[:count]:
            del self.sessions[session_id]