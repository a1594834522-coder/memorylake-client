"""
Claude Memory SDK - Python客户端库

一个用于与Claude Memory Q&A API交互的Python SDK，支持智能记忆功能。
"""

from .client import ClaudeMemoryClient
from .exceptions import (
    ClaudeMemoryError,
    APIError,
    SessionError,
    MemoryError,
    ConfigurationError
)
from .models import (
    QuestionRequest,
    QuestionResponse,
    MemoryViewRequest,
    MemoryViewResponse,
    MemoryCreateRequest,
    MemoryResponse,
    SessionInfo,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryBackupRequest,
    MemoryBackupResponse,
    MemoryOrganizeRequest,
    MemoryOrganizeResponse,
    SessionListResponse
)

__version__ = "1.0.0"
__author__ = "Claude Memory SDK Team"
__email__ = "support@example.com"
__description__ = "Python SDK for Claude Memory Q&A API"

__all__ = [
    "ClaudeMemoryClient",
    "ClaudeMemoryError",
    "APIError",
    "SessionError",
    "MemoryError",
    "ConfigurationError",
    "QuestionRequest",
    "QuestionResponse",
    "MemoryViewRequest",
    "MemoryViewResponse",
    "MemoryCreateRequest",
    "MemoryResponse",
    "SessionInfo",
    "MemorySearchRequest",
    "MemorySearchResponse",
    "MemoryBackupRequest",
    "MemoryBackupResponse",
    "MemoryOrganizeRequest",
    "MemoryOrganizeResponse",
    "SessionListResponse"
]