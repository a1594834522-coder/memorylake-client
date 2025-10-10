"""
Claude Memory Server - 服务端包

Claude Memory Q&A API 的服务端实现，提供FastAPI服务器和记忆管理功能。
"""

from .app import create_app
from .config import ServerConfig
from .memory_manager import MemoryManager
from .session_manager import SessionManager

__version__ = "1.0.0"
__author__ = "Claude Memory Server Team"
__description__ = "Server implementation for Claude Memory Q&A API"

__all__ = [
    "create_app",
    "ServerConfig",
    "MemoryManager",
    "SessionManager"
]