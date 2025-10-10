"""
Claude Memory Server 配置管理
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class ServerConfig(BaseModel):
    """服务器配置类"""

    # API配置
    anthropic_api_key: str = Field(default="DUMMY", description="Anthropic API密钥")
    anthropic_base_url: str = Field(
        default="http://107.155.48.191:8000/anthropic",
        description="Anthropic API基础URL"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-5",
        description="使用的Claude模型"
    )

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机地址")
    port: int = Field(default=8002, description="服务器端口")
    debug: bool = Field(default=False, description="调试模式")

    # 记忆配置
    memory_dir: str = Field(default="./memory", description="记忆存储目录")
    memory_system_prompt: str = Field(
        default="""You are a helpful AI assistant with memory capabilities.

MEMORY PROTOCOL:
1. ALWAYS CHECK YOUR MEMORY BEFORE ANSWERING QUESTIONS.
2. Store important information about the user and your conversations in memory files.
3. Before responding, check memory to personalize your responses and maintain context.
4. Keep memories up-to-date - remove outdated info, add new details as you learn them.
5. Use XML format for structured information storage.

IMPORTANT: Do not mention your memory tool or what you are writing in it to the user, unless they ask specifically about it.

Available memory commands:
- view: Check memory directory or file contents
- create: Create new memory files
- str_replace: Replace text in existing files
- insert: Insert text at specific lines
- delete: Delete files or directories
- rename: Rename or move files

Always use the memory tool to store important user information and preferences.""",
        description="记忆系统提示词"
    )

    # 性能配置
    max_tokens: int = Field(default=2048, description="最大token数")
    request_timeout: int = Field(default=60, description="请求超时时间（秒）")
    max_sessions: int = Field(default=1000, description="最大会话数")

    # 安全配置
    allowed_origins: list[str] = Field(
        default=["*"],
        description="允许的CORS来源"
    )
    require_auth: bool = Field(default=False, description="是否需要认证")
    auth_token: Optional[str] = Field(None, description="认证令牌")

    class Config:
        env_file = ".env"
        env_prefix = "CLAUDE_MEMORY_"

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """从环境变量加载配置"""
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "DUMMY"),
            anthropic_base_url=os.getenv(
                "ANTHROPIC_BASE_URL",
                "http://107.155.48.191:8000/anthropic"
            ),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8002")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            memory_dir=os.getenv("MEMORY_DIR", "./memory"),
            max_tokens=int(os.getenv("MAX_TOKENS", "2048")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "60")),
            max_sessions=int(os.getenv("MAX_SESSIONS", "1000")),
            require_auth=os.getenv("REQUIRE_AUTH", "false").lower() == "true",
            auth_token=os.getenv("AUTH_TOKEN"),
        )