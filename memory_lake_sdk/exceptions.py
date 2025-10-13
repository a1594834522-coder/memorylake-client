#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Lake SDK 异常类定义

定义了 SDK 中使用的各种异常类型，用于更好地处理错误情况。
"""


class MemorySDKError(Exception):
    """Memory SDK 基础异常类

    所有 SDK 相关异常的基类，用于捕获 SDK 层面的错误。
    """
    pass


class MemoryBackendError(MemorySDKError):
    """记忆存储后端异常

    当记忆存储后端操作失败时抛出此异常。
    """
    pass


class MemoryPathError(MemoryBackendError):
    """记忆路径异常

    当记忆路径无效或不安全时抛出此异常。
    主要用于防止路径遍历攻击。
    """
    pass


class MemoryFileOperationError(MemoryBackendError):
    """记忆文件操作异常

    当记忆文件操作（创建、读取、写入、删除等）失败时抛出此异常。
    """
    pass


class MemoryValidationError(MemorySDKError):
    """记忆数据验证异常

    当记忆数据不符合预期格式或包含无效内容时抛出此异常。
    """
    pass


class MemoryAPIError(MemorySDKError):
    """记忆 API 调用异常

    当调用 Anthropic API 时发生错误时抛出此异常。
    """
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class MemoryConfigurationError(MemorySDKError):
    """记忆配置异常

    当SDK配置不正确时抛出此异常。
    """
    pass


class MemoryAuthenticationError(MemoryAPIError):
    """记忆认证异常

    当API认证失败时抛出此异常。
    """
    def __init__(self, message: str = "API认证失败"):
        super().__init__(message, status_code=401)


class MemoryRateLimitError(MemoryAPIError):
    """记忆速率限制异常

    当API调用超过速率限制时抛出此异常。
    """
    def __init__(self, message: str = "API调用超过速率限制"):
        super().__init__(message, status_code=429)


class MemoryTimeoutError(MemoryAPIError):
    """记忆超时异常

    当API调用超时时抛出此异常。
    """
    pass


class MemoryContextError(MemorySDKError):
    """记忆上下文异常

    当对话上下文处理出错时抛出此异常。
    """
    pass


class MemoryToolError(MemorySDKError):
    """记忆工具异常

    当记忆工具执行失败时抛出此异常。
    """
    pass
