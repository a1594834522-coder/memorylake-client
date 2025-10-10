"""
Claude Memory SDK 核心客户端
"""

import json
import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    QuestionRequest,
    QuestionResponse,
    MemoryViewRequest,
    MemoryViewResponse,
    MemoryCreateRequest,
    MemoryResponse,
    SessionInfo,
    MemoryFileInfo,
    MemoryListResponse,
    APIInfo,
    ClientConfig,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryBackupRequest,
    MemoryBackupResponse,
    MemoryOrganizeRequest,
    MemoryOrganizeResponse,
    SessionListResponse
)
from .conversation import ConversationManager, Conversation
from .memory_operations import MemoryOperations
from .exceptions import (
    ClaudeMemoryError,
    APIError,
    SessionError,
    MemoryError,
    ConfigurationError,
    NetworkError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    TimeoutError
)


class ClaudeMemoryClient:
    """
    Claude Memory API 客户端

    提供与Claude Memory Q&A API交互的完整功能，包括：
    - 智能问答
    - 记忆管理
    - 会话管理
    - 错误处理和重试机制
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8002",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
        config: Optional[ClientConfig] = None
    ):
        """
        初始化Claude Memory客户端

        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            headers: 自定义请求头
            config: 客户端配置对象
        """
        """
        初始化Claude Memory客户端

        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            headers: 自定义请求头
            config: 客户端配置对象
        """
        if config:
            self.config = config
        else:
            self.config = ClientConfig(
                base_url=base_url,
                timeout=timeout,
                max_retries=max_retries,
                retry_delay=retry_delay,
                headers=headers or {}
            )

        self.session_id: Optional[str] = None
        self.logger = self._setup_logger()
        self._setup_session()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _setup_session(self):
        """设置HTTP会话"""
        self.session = requests.Session()

        # 设置重试策略
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认请求头
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": f"ClaudeMemorySDK/1.0.0"
        }
        default_headers.update(self.config.headers)
        self.session.headers.update(default_headers)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            params: 查询参数

        Returns:
            响应数据

        Raises:
            ClaudeMemoryError: API相关错误
        """
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            self.logger.debug(f"Making {method} request to {url}")

            if method.upper() == "GET":
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.timeout
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    url,
                    json=data,
                    params=params,
                    timeout=self.config.timeout
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    url,
                    params=params,
                    timeout=self.config.timeout
                )
            else:
                raise ConfigurationError(f"Unsupported HTTP method: {method}")

            return self._handle_response(response)

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request to {url} timed out after {self.config.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Failed to connect to {url}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理HTTP响应

        Args:
            response: requests响应对象

        Returns:
            响应数据字典

        Raises:
            ClaudeMemoryError: 根据状态码抛出相应异常
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"raw_response": response.text}

        if response.status_code == 200:
            return response_data
        elif response.status_code == 400:
            raise APIError("Bad Request", response.status_code, response_data)
        elif response.status_code == 401:
            raise AuthenticationError("Unauthorized", response.status_code, response_data)
        elif response.status_code == 403:
            raise AuthenticationError("Forbidden", response.status_code, response_data)
        elif response.status_code == 404:
            raise APIError("Not Found", response.status_code, response_data)
        elif response.status_code == 429:
            raise RateLimitError("Rate Limit Exceeded", response.status_code, response_data)
        elif response.status_code >= 500:
            raise ServerError("Server Error", response.status_code, response_data)
        else:
            raise APIError(
                f"Unexpected status code: {response.status_code}",
                response.status_code,
                response_data
            )

    # ==================== API信息 ====================

    def get_api_info(self) -> APIInfo:
        """
        获取API基本信息

        Returns:
            API信息对象
        """
        response_data = self._make_request("GET", "/")
        return APIInfo(**response_data)

    # ==================== 问答接口 ====================

    def ask(
        self,
        question: str,
        session_id: Optional[str] = None
    ) -> QuestionResponse:
        """
        向Claude提问

        Args:
            question: 用户问题
            session_id: 会话ID，如果为None则使用客户端的session_id或创建新会话

        Returns:
            问题响应对象
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        # 确定使用的会话ID - 简化逻辑
        effective_session_id = session_id or self.session_id

        request_data = QuestionRequest(
            question=question,
            session_id=effective_session_id
        )

        response_data = self._make_request(
            "POST",
            "/ask",
            data=request_data.model_dump(exclude_none=True)
        )

        # 更新客户端会话ID缓存
        self.session_id = response_data.get("session_id")

        response = QuestionResponse(
            answer=response_data.get("answer", ""),
            session_id=response_data.get("session_id", ""),
            memory_files=response_data.get("memory_files", []),
            timestamp=datetime.now()
        )

        self.logger.info(f"Asked question: {question[:50]}...")
        return response

    # ==================== 记忆管理 ====================

    def view_memory(self, path: str = "/memories") -> MemoryViewResponse:
        """
        查看记忆内容

        Args:
            path: 查看路径，默认为记忆根目录

        Returns:
            记忆查看响应对象
        """
        request_data = MemoryViewRequest(path=path)

        response_data = self._make_request(
            "POST",
            "/memory/view",
            data=request_data.model_dump()
        )

        return MemoryViewResponse(
            contents=response_data.get("contents", ""),
            path=response_data.get("path", path),
            timestamp=datetime.now()
        )

    def list_memory_files(self) -> MemoryListResponse:
        """
        列出所有记忆文件

        Returns:
            记忆文件列表响应对象
        """
        response_data = self._make_request("GET", "/memory/files")

        files = []
        for file_name in response_data.get("files", []):
            file_info = MemoryFileInfo(
                name=file_name,
                path=f"/memories/{file_name}"
            )
            files.append(file_info)

        return MemoryListResponse(
            files=files,
            total_count=len(files),
            timestamp=datetime.now()
        )

    def create_memory_file(self, path: str, content: str) -> MemoryResponse:
        """
        创建记忆文件

        Args:
            path: 文件路径
            content: 文件内容

        Returns:
            记忆操作响应对象
        """
        if not path.startswith("/memories"):
            raise ValueError("Path must start with /memories")

        request_data = MemoryCreateRequest(path=path, content=content)

        response_data = self._make_request(
            "POST",
            "/memory/create",
            data=request_data.model_dump()
        )

        return MemoryResponse(
            message=response_data.get("message", ""),
            path=response_data.get("path", path),
            timestamp=datetime.now()
        )

    def delete_memory_file(self, path: str) -> MemoryResponse:
        """
        删除记忆文件

        Args:
            path: 文件路径

        Returns:
            记忆操作响应对象
        """
        if not path.startswith("/memories"):
            raise ValueError("Path must start with /memories")

        response_data = self._make_request("DELETE", f"/memory{path}")

        return MemoryResponse(
            message=response_data.get("message", ""),
            path=path,
            timestamp=datetime.now()
        )

    # ==================== 会话管理 ====================

    def get_session_info(self, session_id: Optional[str] = None) -> SessionInfo:
        """
        获取会话信息

        Args:
            session_id: 会话ID，如果为None则使用客户端的session_id

        Returns:
            会话信息对象
        """
        effective_session_id = session_id or self.session_id

        if not effective_session_id:
            raise SessionError("No session ID provided")

        response_data = self._make_request("GET", f"/sessions/{effective_session_id}")

        return SessionInfo(
            session_id=response_data.get("session_id", effective_session_id),
            message_count=response_data.get("message_count", 0),
            memory_files=response_data.get("memory_files", []),
            created_at=datetime.fromisoformat(response_data.get("created_at", "")) if response_data.get("created_at") else None,
            last_activity=datetime.fromisoformat(response_data.get("last_activity", "")) if response_data.get("last_activity") else None,
            timestamp=datetime.now()
        )

    def clear_session(self, session_id: Optional[str] = None) -> str:
        """
        清除会话历史

        Args:
            session_id: 会话ID，如果为None则使用客户端的session_id

        Returns:
            操作结果消息
        """
        effective_session_id = session_id or self.session_id

        if not effective_session_id:
            raise SessionError("No session ID provided")

        response_data = self._make_request("DELETE", f"/sessions/{effective_session_id}")

        # 如果清除的是当前会话，重置客户端会话ID
        if effective_session_id == self.session_id:
            self.session_id = None

        return response_data.get("message", "Session cleared")

    def delete_session(self, session_id: Optional[str] = None) -> str:
        """
        完全删除会话

        Args:
            session_id: 会话ID，如果为None则使用客户端的session_id

        Returns:
            操作结果消息
        """
        effective_session_id = session_id or self.session_id

        if not effective_session_id:
            raise SessionError("No session ID provided")

        response_data = self._make_request("DELETE", f"/sessions/{effective_session_id}/delete")

        # 如果删除的是当前会话，重置客户端会话ID
        if effective_session_id == self.session_id:
            self.session_id = None

        return response_data.get("message", "Session deleted")

    def list_sessions(self) -> SessionListResponse:
        """
        列出所有活跃会话

        Returns:
            会话列表响应对象
        """
        response_data = self._make_request("GET", "/sessions")

        sessions = []
        for session_data in response_data.get("sessions", []):
            session = SessionInfo(
                session_id=session_data.get("session_id", ""),
                message_count=session_data.get("message_count", 0),
                memory_files=[],
                created_at=datetime.fromisoformat(session_data.get("created_at", "")) if session_data.get("created_at") else None,
                last_activity=datetime.fromisoformat(session_data.get("last_activity", "")) if session_data.get("last_activity") else None
            )
            sessions.append(session)

        return SessionListResponse(
            sessions=sessions,
            total=response_data.get("total", 0),
            timestamp=datetime.now()
        )

    def start_new_session(self) -> str:
        """
        开始新会话（重置客户端会话ID）

        Returns:
            新会话ID
        """
        # 发送一个简单问题来创建新会话
        response = self.ask("Hello")
        return response.session_id

    # ==================== 便利方法 ====================

    def chat(self, message: str) -> str:
        """
        简化的聊天接口

        Args:
            message: 用户消息

        Returns:
            Claude的回答文本
        """
        response = self.ask(message)
        return response.answer

    def remember(self, key: str, value: str) -> bool:
        """
        记住信息（便利方法）

        Args:
            key: 信息键
            value: 信息值

        Returns:
            是否成功
        """
        try:
            content = f"{key}: {value}"
            self.create_memory_file(f"/memories/{key}.txt", content)
            return True
        except Exception:
            return False

    def recall(self, key: str) -> Optional[str]:
        """
        回忆信息（便利方法）

        Args:
            key: 信息键

        Returns:
            信息值，如果不存在则返回None
        """
        try:
            response = self.view_memory(f"/memories/{key}.txt")
            lines = response.contents.strip().split('\n')
            for line in lines:
                if line.startswith(f"{key}:"):
                    return line[len(f"{key}:"):].strip()
            return None
        except Exception:
            return None

    # ==================== 批量操作 ====================

    def ask_batch(self, questions: List[str]) -> List[QuestionResponse]:
        """
        批量提问

        Args:
            questions: 问题列表

        Returns:
            响应列表
        """
        responses = []
        for question in questions:
            try:
                response = self.ask(question)
                responses.append(response)
            except Exception as e:
                self.logger.error(f"Failed to ask question '{question}': {e}")
                # 创建一个错误响应
                error_response = QuestionResponse(
                    answer=f"Error: {str(e)}",
                    session_id=self.session_id or "",
                    memory_files=[]
                )
                responses.append(error_response)

        return responses

    # ==================== 高级记忆功能 ====================

    def search_memory(self, query: str, file_pattern: str = "*") -> MemorySearchResponse:
        """
        搜索记忆内容

        Args:
            query: 搜索关键词
            file_pattern: 文件模式，支持通配符

        Returns:
            搜索结果响应对象
        """
        request_data = MemorySearchRequest(
            query=query,
            file_pattern=file_pattern
        )

        response_data = self._make_request(
            "POST",
            "/memory/search",
            data=request_data.model_dump()
        )

        # 转换搜索结果
        results = []
        for result_data in response_data.get("results", []):
            result = {
                "file": result_data.get("file", ""),
                "path": result_data.get("path", ""),
                "matches": result_data.get("matches", []),
                "match_count": result_data.get("match_count", 0)
            }
            results.append(result)

        return MemorySearchResponse(
            results=results,
            total_matches=response_data.get("total_matches", 0),
            timestamp=datetime.now()
        )

    def backup_memory(self, format: str = "json") -> MemoryBackupResponse:
        """
        备份记忆内容

        Args:
            format: 备份格式 ("json" 或 "zip")

        Returns:
            备份响应对象
        """
        request_data = MemoryBackupRequest(format=format)

        response_data = self._make_request(
            "POST",
            "/memory/backup",
            data=request_data.model_dump()
        )

        return MemoryBackupResponse(
            backup_data=response_data.get("backup_data"),
            download_url=response_data.get("download_url"),
            message=response_data.get("message", ""),
            timestamp=datetime.now()
        )

    def organize_memory(self, rules: Dict[str, str], dry_run: bool = True) -> MemoryOrganizeResponse:
        """
        整理记忆文件

        Args:
            rules: 整理规则，正则模式 -> 目标目录
            dry_run: 是否为预览模式

        Returns:
            整理响应对象
        """
        request_data = MemoryOrganizeRequest(
            rules=rules,
            dry_run=dry_run
        )

        response_data = self._make_request(
            "POST",
            "/memory/organize",
            data=request_data.model_dump()
        )

        return MemoryOrganizeResponse(
            moved_files=response_data.get("moved_files", []),
            message=response_data.get("message", ""),
            timestamp=datetime.now()
        )

    def export_memory(self, format: str = "text") -> str:
        """
        导出记忆内容（已弃用，请使用 backup_memory）

        Args:
            format: 导出格式 ("text" 或 "json")

        Returns:
            导出的记忆内容
        """
        # 使用新的备份API
        if format.lower() == "json":
            backup_response = self.backup_memory("json")
            return backup_response.backup_data or "{}"
        else:
            # 保持原有的文本格式逻辑
            files_response = self.list_memory_files()
            memory_text = []
            memory_text.append("=== Claude Memory Export ===")
            memory_text.append(f"Exported at: {datetime.now().isoformat()}")
            memory_text.append(f"Total files: {len(files_response.files)}")
            memory_text.append("")

            for file_info in files_response.files:
                memory_text.append(f"--- {file_info.name} ---")
                try:
                    content_response = self.view_memory(file_info.path)
                    memory_text.append(content_response.contents)
                except Exception as e:
                    memory_text.append(f"Error: {str(e)}")
                memory_text.append("")

            return "\n".join(memory_text)

    # ==================== 清理方法 ====================

    def close(self):
        """关闭客户端会话"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()