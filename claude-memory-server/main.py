"""
Claude Memory Server 启动脚本
"""

import uvicorn
from claude_memory_server import create_app, ServerConfig


def main():
    """启动服务器"""
    # 从环境变量或默认配置加载
    config = ServerConfig.from_env()

    # 创建应用
    app = create_app(config)

    # 启动服务器
    print(f"🚀 Starting Claude Memory Server")
    print(f"📍 Host: {config.host}")
    print(f"🔌 Port: {config.port}")
    print(f"🧠 Memory Directory: {config.memory_dir}")
    print(f"🤖 Model: {config.anthropic_model}")
    print(f"🔗 API URL: {config.anthropic_base_url}")

    if config.debug:
        print("🐛 Debug mode enabled")

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info" if not config.debug else "debug"
    )


if __name__ == "__main__":
    main()