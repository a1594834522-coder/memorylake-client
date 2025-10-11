# Claude Memory SDK

[![PyPI version](https://badge.fury.io/py/claude-memory-sdk.svg)](https://badge.fury.io/py/claude-memory-sdk)
[![Python versions](https://img.shields.io/pypi/pyversions/claude-memory-sdk.svg)](https://pypi.org/project/claude-memory-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/memorylake/claude-memory-sdk/workflows/CI/badge.svg)](https://github.com/memorylake/claude-memory-sdk/actions)

一个用于简化开发者对 Claude Memory Tool 使用的 Python SDK。提供强大的可扩展性，支持多种记忆存储方式。

## ✨ 特性

- 🧠 **智能记忆管理**: 自动处理 Claude 的记忆工具调用，简化开发流程
- 🔌 **可插拔存储**: 支持文件系统、数据库等多种存储后端
- 🛡️ **安全可靠**: 内置路径安全验证，防止路径遍历攻击
- 📦 **易于分发**: 可通过 `pip install` 轻松安装
- 🚀 **开箱即用**: 提供简洁的 API 接口，快速集成到现有项目
- 🧪 **完整测试**: 包含全面的单元测试，确保代码质量

## 📦 安装

### 基础安装

```bash
pip install claude-memory-sdk
```

### 开发安装

```bash
# 克隆仓库
git clone https://github.com/memorylake/claude-memory-sdk.git
cd claude-memory-sdk

# 安装开发依赖
pip install -e .[dev]
```

### 测试安装

```bash
pip install -e .[test]
```

## 🚀 快速开始

### 环境变量配置

在使用 SDK 之前，您可以配置以下环境变量：

```bash
# 必需：API 密钥
export ANTHROPIC_API_KEY="your-api-key-here"

# 可选：指定模型（默认为 claude-4-sonnet）
export ANTHROPIC_MODEL="claude-4-sonnet"

# 可选：自定义 API 基础 URL（用于代理或私有部署）
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 基础对话

```python
import os
from claude_memory_sdk import ClaudeMemoryClient

# 设置 API 密钥（也可以通过环境变量设置）
os.environ["ANTHROPIC_API_KEY"] = "your-api-key-here"

# 初始化客户端（会自动从环境变量读取配置）
client = ClaudeMemoryClient()

# 开始对话
response = client.chat("你好，请记住我喜欢喝咖啡")
print(response)

# Claude 会自动管理记忆，后续对话会记住这个信息
response2 = client.chat("我之前说过我喜欢什么？")
print(response2)  # 会提到咖啡
```

### 使用自定义配置

```python
from claude_memory_sdk import ClaudeMemoryClient

# 通过参数直接配置
client = ClaudeMemoryClient(
    api_key="your-api-key",
    base_url="https://custom-api.example.com",  # 自定义 API 端点
    model="claude-3-opus-20240229",            # 指定模型
    max_tokens=4096                             # 自定义令牌限制
)

response = client.chat("你好")
print(response)
```

### 手动记忆管理

```python   
from claude_memory_sdk import ClaudeMemoryClient        

client = ClaudeMemoryClient()

# 添加用户偏好
client.add_memory("/memories/preferences.xml", """
<user_preferences>
    <name>张三</name>
    <language>中文</language>
    <favorite_drink>咖啡</favorite_drink>
    <technical_level>中级</technical_level>
</user_preferences>
""")

# 查看记忆
preferences = client.get_memory("/memories/preferences.xml")
print(preferences)

# 在对话中使用记忆
response = client.chat("根据我的偏好，推荐一些适合我的学习资源")
print(response)
```

### 自定义存储后端

```python
from claude_memory_sdk import ClaudeMemoryClient, BaseMemoryBackend
import sqlite3

class DatabaseMemoryBackend(BaseMemoryBackend):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        # 初始化数据库表
        pass

    def view(self, path: str, view_range=None) -> str:
        # 实现查看功能
        pass

    def create(self, path: str, file_text: str) -> None:
        # 实现创建功能
        pass

    # 实现其他必需方法...

# 使用自定义后端
custom_backend = DatabaseMemoryBackend("./memory.db")
client = ClaudeMemoryClient(memory_backend=custom_backend)
```

## 📖 核心概念

### 记忆存储哲学

- **数据主权**: 记忆数据存储在用户环境中，SDK 不接触用户数据
- **责任分离**: SDK 提供处理记忆的能力，但不负责保管记忆本身
- **可插拔性**: 通过抽象接口支持多种存储方式

### 安全性

- **路径验证**: 所有路径必须以 `/memories` 开头
- **遍历防护**: 防止通过 `../` 等方式访问系统文件
- **权限控制**: 限制所有操作在指定基础目录内

## 🎯 API 参考

### ClaudeMemoryClient

主要的客户端类，提供对话和记忆管理功能。

#### 初始化参数

- `api_key` (str, optional): Anthropic API 密钥，如果为 None 则从环境变量 `ANTHROPIC_API_KEY` 获取
- `base_url` (str, optional): API 基础 URL，如果为 None 则从环境变量 `ANTHROPIC_BASE_URL` 获取
- `memory_backend` (BaseMemoryBackend, optional): 自定义记忆后端
- `model` (str, optional): 使用的模型，如果为 None 则从环境变量 `ANTHROPIC_MODEL` 获取，默认为 "claude-4-sonnet"
- `max_tokens` (int): 最大生成令牌数，默认为 2048
- `system_prompt` (str, optional): 自定义系统提示
- `context_management` (dict, optional): 上下文管理配置

#### 主要方法

##### `chat(user_input: str) -> str`

发送消息并获得回复，自动处理记忆工具调用。

```python
response = client.chat("你好，今天天气怎么样？")
```

##### `add_memory(path: str, content: str) -> None`

添加新的记忆文件。

```python
client.add_memory("/memories/notes.txt", "这是我的笔记内容")
```

##### `get_memory(path: str, view_range: tuple=None) -> str`

获取记忆文件内容。

```python
content = client.get_memory("/memories/notes.txt")
partial = client.get_memory("/memories/notes.txt", (1, 10))  # 前10行
```

##### `delete_memory(path: str) -> None`

删除记忆文件。

```python
client.delete_memory("/memories/notes.txt")
```

##### `clear_all_memories() -> None`

清除所有记忆数据。

```python
client.clear_all_memories()
```

##### `clear_conversation_history() -> None`

清除对话历史记录。

```python
client.clear_conversation_history()
```

### BaseMemoryBackend

记忆存储后端的抽象基类，所有自定义后端都需要继承此类。

#### 抽象方法

- `view(path: str, view_range: tuple=None) -> str`: 查看路径内容
- `create(path: str, file_text: str) -> None`: 创建新文件
- `str_replace(path: str, old_str: str, new_str: str) -> None`: 字符串替换
- `insert(path: str, insert_line: int, insert_text: str) -> None`: 行插入
- `delete(path: str) -> None`: 删除路径
- `rename(old_path: str, new_path: str) -> None`: 重命名路径

## 🔧 配置选项

### 环境变量

- `ANTHROPIC_API_KEY`: Anthropic API 密钥（必需）
- `ANTHROPIC_MODEL`: 默认使用的 Claude 模型（可选，默认为 claude-4-sonnet）
- `ANTHROPIC_BASE_URL`: 自定义 API 基础 URL（可选，用于代理或私有部署）

### 上下文管理

SDK 支持自动上下文管理，当对话过长时自动清理旧的工具调用结果：

```python
client = ClaudeMemoryClient(
    context_management={
        "edits": [
            {
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 30000},
                "keep": {"type": "tool_uses", "value": 3},
                "exclude_tools": ["memory"],  # 保留记忆工具调用
            }
        ]
    }
)
```

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=claude_memory_sdk --cov-report=html

# 运行特定测试
pytest claude_memory_sdk/tests/test_client.py
```

## 📁 项目结构

```
claude_memory_sdk/
├── claude_memory_sdk/
│   ├── __init__.py          # 包初始化
│   ├── client.py            # 主客户端类
│   ├── memory_backend.py    # 记忆后端实现
│   └── exceptions.py        # 自定义异常
│
├── examples/                # 示例代码
│   ├── basic_chat.py        # 基础聊天示例
│   ├── manage_memory.py     # 记忆管理示例
│   └── custom_backend.py    # 自定义后端示例
│
├── tests/                   # 测试文件
│   ├── test_client.py       # 客户端测试
│   └── test_memory_backend.py # 后端测试
│
├── setup.py                 # 安装配置
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
└── README.md               # 项目文档
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/memorylake/claude-memory-sdk.git
cd claude-memory-sdk

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e .[dev]

# 安装 pre-commit 钩子
pre-commit install
```

### 代码规范

- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查
- 使用 mypy 进行类型检查

```bash
# 运行所有检查
black claude_memory_sdk/
isort claude_memory_sdk/
flake8 claude_memory_sdk/
mypy claude_memory_sdk/
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [Claude API 文档](https://docs.anthropic.com/claude/reference)
- [Memory Tool 文档](https://docs.anthropic.com/claude/docs/memory-tool)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)

## 🆘 支持

如果您遇到问题或有疑问：

1. 查看 [文档](https://github.com/memorylake/claude-memory-sdk/docs)
2. 搜索 [已有 Issues](https://github.com/memorylake/claude-memory-sdk/issues)
3. 创建 [新 Issue](https://github.com/memorylake/claude-memory-sdk/issues/new)
4. 联系我们: team@memorylake.ai

## 🎉 致谢

感谢 Anthropic 提供强大的 Claude API 和记忆工具功能。

---

**Claude Memory SDK** - 让 Claude 的记忆能力触手可及 🧠