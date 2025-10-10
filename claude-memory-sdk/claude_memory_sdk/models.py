"""
Claude Memory SDK 数据模型
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class QuestionRequest(BaseModel):
    """问题请求模型"""
    question: str = Field(..., description="用户问题", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID，用于延续会话")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "我叫张三，喜欢编程",
                "session_id": "session_1234567890_abcdef"
            }
        }


class QuestionResponse(BaseModel):
    """问题响应模型"""
    answer: str = Field(..., description="Claude的回答")
    session_id: str = Field(..., description="会话ID")
    memory_files: List[str] = Field(default_factory=list, description="关联的记忆文件列表")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "你好张三！我记住了你喜欢编程。有什么编程相关的问题我可以帮助你吗？",
                "session_id": "session_1234567890_abcdef",
                "memory_files": ["user_profile.xml"]
            }
        }


class MemoryViewRequest(BaseModel):
    """记忆查看请求模型"""
    path: str = Field(default="/memories", description="查看的路径，默认为记忆根目录")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "/memories"
            }
        }


class MemoryViewResponse(BaseModel):
    """记忆查看响应模型"""
    contents: str = Field(..., description="记忆内容")
    path: str = Field(..., description="请求的路径")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "contents": "Directory: /memories\n- user_profile.xml\n- preferences.xml",
                "path": "/memories"
            }
        }


class MemoryCreateRequest(BaseModel):
    """记忆创建请求模型"""
    path: str = Field(..., description="文件路径")
    content: str = Field(..., description="文件内容")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "/memories/notes.txt",
                "content": "这是一个笔记文件\n包含重要信息"
            }
        }


class MemoryResponse(BaseModel):
    """记忆操作响应模型"""
    message: str = Field(..., description="操作结果消息")
    path: Optional[str] = Field(None, description="相关路径")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "File created successfully at /memories/notes.txt",
                "path": "/memories/notes.txt"
            }
        }


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(..., description="会话ID")
    message_count: int = Field(..., description="消息数量")
    memory_files: List[str] = Field(default_factory=list, description="关联的记忆文件")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_1234567890_abcdef",
                "message_count": 5,
                "memory_files": ["user_profile.xml", "preferences.xml"]
            }
        }


class MemoryFileInfo(BaseModel):
    """记忆文件信息模型"""
    name: str = Field(..., description="文件名")
    path: str = Field(..., description="文件路径")
    size: Optional[int] = Field(None, description="文件大小（字节）")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    modified_at: Optional[datetime] = Field(None, description="修改时间")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "user_profile.xml",
                "path": "/memories/user_profile.xml",
                "size": 1024
            }
        }


class MemoryListResponse(BaseModel):
    """记忆文件列表响应模型"""
    files: List[MemoryFileInfo] = Field(default_factory=list, description="记忆文件列表")
    total_count: int = Field(default=0, description="文件总数")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "name": "user_profile.xml",
                        "path": "/memories/user_profile.xml",
                        "size": 1024
                    }
                ],
                "total_count": 1
            }
        }


class APIInfo(BaseModel):
    """API信息模型"""
    message: str = Field(..., description="API信息")
    version: str = Field(..., description="API版本")
    status: str = Field(default="active", description="API状态")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Claude Memory Q&A API",
                "version": "1.0.0",
                "status": "active"
            }
        }


class ClientConfig(BaseModel):
    """客户端配置模型"""
    base_url: str = Field(default="http://localhost:8002", description="API基础URL")
    timeout: int = Field(default=30, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟（秒）")
    headers: Dict[str, str] = Field(default_factory=dict, description="自定义请求头")

    class Config:
        json_schema_extra = {
            "example": {
                "base_url": "http://localhost:8002",
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 1.0,
                "headers": {
                    "User-Agent": "ClaudeMemorySDK/1.0.0"
                }
            }
        }


class MemorySearchRequest(BaseModel):
    """记忆搜索请求模型"""
    query: str = Field(..., description="搜索关键词", min_length=1)
    file_pattern: str = Field(default="*", description="文件模式，支持通配符")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Python",
                "file_pattern": "*.txt"
            }
        }


class MemorySearchResult(BaseModel):
    """记忆搜索结果模型"""
    file: str = Field(..., description="文件名")
    path: str = Field(..., description="文件路径")
    matches: List[Dict[str, Any]] = Field(..., description="匹配结果列表")
    match_count: int = Field(..., description="匹配数量")

    class Config:
        json_schema_extra = {
            "example": {
                "file": "notes.txt",
                "path": "/memories/notes.txt",
                "matches": [
                    {
                        "line_number": 1,
                        "content": "我喜欢Python编程",
                        "match_start": 3
                    }
                ],
                "match_count": 1
            }
        }


class MemorySearchResponse(BaseModel):
    """记忆搜索响应模型"""
    results: List[MemorySearchResult] = Field(default_factory=list, description="搜索结果列表")
    total_matches: int = Field(default=0, description="总匹配数量")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "file": "notes.txt",
                        "path": "/memories/notes.txt",
                        "matches": [
                            {
                                "line_number": 1,
                                "content": "我喜欢Python编程",
                                "match_start": 3
                            }
                        ],
                        "match_count": 1
                    }
                ],
                "total_matches": 1
            }
        }


class MemoryBackupRequest(BaseModel):
    """记忆备份请求模型"""
    format: str = Field(default="json", description="备份格式：json 或 zip")

    class Config:
        json_schema_extra = {
            "example": {
                "format": "json"
            }
        }


class MemoryBackupResponse(BaseModel):
    """记忆备份响应模型"""
    backup_data: Optional[str] = Field(None, description="备份数据（JSON格式）")
    download_url: Optional[str] = Field(None, description="下载链接（ZIP格式）")
    message: str = Field(..., description="操作结果消息")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "backup_data": '{"backup_info": {...}}',
                "message": "成功备份 5 个记忆文件"
            }
        }


class MemoryOrganizeRequest(BaseModel):
    """记忆整理请求模型"""
    rules: Dict[str, str] = Field(..., description="整理规则：正则模式 -> 目标目录")
    dry_run: bool = Field(default=True, description="是否为预览模式")

    class Config:
        json_schema_extra = {
            "example": {
                "rules": {
                    r".*profile.*": "/memories/personal/",
                    r".*project.*": "/memories/work/"
                },
                "dry_run": True
            }
        }


class MemoryOrganizeResponse(BaseModel):
    """记忆整理响应模型"""
    moved_files: List[str] = Field(default_factory=list, description="移动的文件列表")
    message: str = Field(..., description="操作结果消息")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "moved_files": [
                    "/memories/profile.txt -> /memories/personal/profile.txt"
                ],
                "message": "预览模式完成，处理了 1 个文件"
            }
        }


class SessionListResponse(BaseModel):
    """会话列表响应模型"""
    sessions: List[SessionInfo] = Field(default_factory=list, description="会话列表")
    total: int = Field(default=0, description="总会话数量")
    timestamp: Optional[datetime] = Field(None, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "session_1234567890_abcdef",
                        "message_count": 5
                    }
                ],
                "total": 1
            }
        }