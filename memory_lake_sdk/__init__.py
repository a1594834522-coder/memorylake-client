#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Lake SDK

一个用于简化 Claude Memory Tool 使用的 Python SDK。
"""

__version__ = "0.3.0"
__author__ = "Memory Lake Team"
__email__ = "team@memorylake.ai"

from .client import MemoryLakeClient
from .memory_backend import BaseMemoryBackend, FileSystemMemoryBackend
from .memory_tool import MemoryBackendTool
from .exceptions import (
    MemorySDKError,
    MemoryBackendError,
    MemoryPathError,
    MemoryFileOperationError,
)

__all__ = [
    "MemoryLakeClient",
    "BaseMemoryBackend",
    "FileSystemMemoryBackend",
    "MemoryBackendTool",
    "MemorySDKError",
    "MemoryBackendError",
    "MemoryPathError",
    "MemoryFileOperationError",
]
