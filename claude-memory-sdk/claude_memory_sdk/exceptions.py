"""
Claude Memory SDK 异常定义
"""


class ClaudeMemoryError(Exception):
    """Claude Memory SDK 基础异常类"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class APIError(ClaudeMemoryError):
    """API调用相关错误"""
    pass


class SessionError(ClaudeMemoryError):
    """会话管理相关错误"""
    pass


class MemoryError(ClaudeMemoryError):
    """记忆操作相关错误"""
    pass


class ConfigurationError(ClaudeMemoryError):
    """配置相关错误"""
    pass


class ValidationError(ClaudeMemoryError):
    """数据验证相关错误"""
    pass


class NetworkError(ClaudeMemoryError):
    """网络连接相关错误"""
    pass


class AuthenticationError(ClaudeMemoryError):
    """认证相关错误"""
    pass


class RateLimitError(ClaudeMemoryError):
    """频率限制相关错误"""
    pass


class ServerError(ClaudeMemoryError):
    """服务器错误"""
    pass


class TimeoutError(ClaudeMemoryError):
    """请求超时错误"""
    pass