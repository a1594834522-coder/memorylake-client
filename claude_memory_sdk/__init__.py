#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Memory SDK

一个用于简化 Claude Memory Tool 使用的 Python SDK。
"""

__version__ = "0.1.0"
__author__ = "Memory Lake Team"
__email__ = "team@memorylake.ai"

from .client import ClaudeMemoryClient
from .memory_backend import BaseMemoryBackend, FileSystemMemoryBackend
from .exceptions import (
    MemorySDKError,
    MemoryBackendError,
    MemoryPathError,
    MemoryFileOperationError,
)

__all__ = [
    "ClaudeMemoryClient",
    "BaseMemoryBackend",
    "FileSystemMemoryBackend",
    "MemorySDKError",
    "MemoryBackendError",
    "MemoryPathError",
    "MemoryFileOperationError",
]