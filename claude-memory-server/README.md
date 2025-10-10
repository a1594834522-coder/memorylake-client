# Claude Memory Server

🧠 Claude Memory Q&A API 服务端实现

Claude Memory Server 是Claude Memory Q&A API的服务端实现，基于FastAPI构建，提供完整的记忆功能和智能问答服务。

## ✨ 主要特性

- 🚀 **FastAPI框架**: 高性能异步Web框架
- 🧠 **智能记忆**: 基于Anthropic Claude的记忆系统
- 💾 **文件系统存储**: 可靠的本地文件存储
- 🔄 **会话管理**: 多用户并发会话支持
- 🛡️ **安全防护**: 路径验证和安全控制
- 📊 **RESTful API**: 标准HTTP接口设计
- ⚙️ **灵活配置**: 环境变量和配置文件支持

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd claude-memory-server

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

#### 方法1: 环境变量

创建 `.env` 文件：

```bash
# API配置
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=http://107.155.48.191:8000/anthropic
ANTHROPIC_MODEL=claude-sonnet-4-5

# 服务器配置
HOST=0.0.0.0
PORT=8002
DEBUG=false

# 记忆配置
MEMORY_DIR=./memory
MAX_TOKENS=2048

# 安全配置
REQUIRE_AUTH=false
AUTH_TOKEN=your_token
```

#### 方法2: 代码配置

修改 `main.py` 中的配置：

```python
from claude_memory_server import ServerConfig

config = ServerConfig(
    anthropic_api_key="your_api_key",
    anthropic_base_url="http://107.155.48.191:8000/anthropic",
    host="0.0.0.0",
    port=8002,
    memory_dir="./memory"
)
```

### 启动服务器

```bash
python3 main.py
```

服务器将在 `http://localhost:8002` 启动。

## 📚 API接口

### 核心接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | 获取API信息 |
| POST | `/ask` | 智能问答接口 |
| GET | `/sessions/{id}` | 获取会话信息 |
| DELETE | `/sessions/{id}` | 清除会话历史 |
| POST | `/memory/view` | 查看记忆内容 |
| GET | `/memory/files` | 列出记忆文件 |
| POST | `/memory/create` | 创建记忆文件 |
| DELETE | `/memory/{path}` | 删除记忆文件 |
| GET | `/stats` | 获取统计信息 |

### 使用示例

#### 问答接口

```bash
curl -X POST "http://localhost:8002/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "我叫张三，喜欢编程"
  }'
```

#### 查看记忆

```bash
curl -X POST "http://localhost:8002/memory/view" \
  -H "Content-Type: application/json" \
  -d '{"path": "/memories"}'
```

#### 列出记忆文件

```bash
curl "http://localhost:8002/memory/files"
```

## 🛠️ 开发指南

### 项目结构

```
claude-memory-server/
├── claude_memory_server/          # 主包
│   ├── __init__.py               # 包初始化
│   ├── app.py                    # FastAPI应用
│   ├── config.py                 # 配置管理
│   └── memory_manager.py         # 记忆管理器
├── main.py                       # 启动脚本
├── requirements.txt              # 依赖列表
└── README.md                     # 说明文档
```

### 添加新接口

1. 在 `app.py` 中添加路由：

```python
@app.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
```

2. 添加对应的模型（如果需要）：

```python
class NewModel(BaseModel):
    field: str
```

### 扩展记忆功能

1. 在 `memory_manager.py` 中添加新方法：

```python
def new_memory_operation(self, param: str) -> str:
    """新的记忆操作"""
    # 实现逻辑
    return "操作结果"
```

2. 在 `app.py` 中添加API端点：

```python
@app.post("/memory/new-operation")
async def new_operation(request: NewRequest):
    result = memory_manager.new_memory_operation(request.param)
    return {"message": result}
```

## ⚙️ 配置选项

### 服务器配置

| 配置项 | 默认值 | 描述 |
|--------|--------|------|
| `host` | `0.0.0.0` | 服务器主机地址 |
| `port` | `8002` | 服务器端口 |
| `debug` | `false` | 调试模式 |

### API配置

| 配置项 | 默认值 | 描述 |
|--------|--------|------|
| `anthropic_api_key` | `DUMMY` | Anthropic API密钥 |
| `anthropic_base_url` | `http://107.155.48.191:8000/anthropic` | API基础URL |
| `anthropic_model` | `claude-sonnet-4-5` | 使用的模型 |
| `max_tokens` | `2048` | 最大token数 |

### 记忆配置

| 配置项 | 默认值 | 描述 |
|--------|--------|------|
| `memory_dir` | `./memory` | 记忆存储目录 |
| `memory_system_prompt` | 内置提示 | 记忆系统提示词 |
| `max_sessions` | `1000` | 最大会话数 |

### 安全配置

| 配置项 | 默认值 | 描述 |
|--------|--------|------|
| `allowed_origins` | `["*"]` | 允许的CORS来源 |
| `require_auth` | `false` | 是否需要认证 |
| `auth_token` | `None` | 认证令牌 |

## 🔧 部署

### Docker部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["python", "main.py"]
```

构建和运行：

```bash
docker build -t claude-memory-server .
docker run -p 8002:8002 claude-memory-server
```

### Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  claude-memory-server:
    build: .
    ports:
      - "8002:8002"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}
      - DEBUG=false
    volumes:
      - ./memory:/app/memory
```

运行：

```bash
docker-compose up -d
```

### 生产部署

使用 Gunicorn：

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker claude_memory_server.app:create_app()
```

## 🔍 监控和日志

### 健康检查

```bash
curl "http://localhost:8002/"
```

### 统计信息

```bash
curl "http://localhost:8002/stats"
```

### 日志配置

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🛡️ 安全考虑

### 路径安全

- 所有文件操作限制在 `/memories` 目录内
- 严格的路径验证防止目录遍历攻击
- URL编码路径检查

### 认证授权

```python
# 启用认证
config = ServerConfig(
    require_auth=True,
    auth_token="your-secure-token"
)
```

### 网络安全

```python
# 限制CORS来源
config = ServerConfig(
    allowed_origins=["https://yourdomain.com"]
)
```

## 🧪 测试

### 单元测试

```python
import pytest
from claude_memory_server import create_app

def test_api_info():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Claude Memory Q&A API" in response.json()["message"]
```

### 集成测试

```python
def test_memory_operations():
    # 测试记忆管理功能
    pass
```

## 📈 性能优化

### 内存管理

- 定期清理过期会话
- 限制并发会话数量
- 优化文件读写操作

### 数据库支持

可以扩展为使用数据库存储：

```python
class DatabaseMemoryManager:
    def __init__(self, db_url: str):
        self.db_url = db_url
        # 数据库连接和配置
```

## 🔗 相关链接

- 📖 [Claude Memory SDK](https://github.com/example/claude-memory-sdk)
- 🐛 [问题反馈](https://github.com/example/claude-memory-server/issues)
- 📧 [邮件支持](mailto:support@example.com)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

*Claude Memory Server - 为AI提供记忆能力的服务端解决方案*