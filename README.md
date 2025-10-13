

## 📦 安装

### 基础安装

```bash
pip install --extra-index-url https://test.pypi.org/simple/ memory-lake-sdk==0.2.0
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
export ANTHROPIC_API_KEY="sk-ant-********"

# 可选：指定模型（默认为 claude-4-sonnet）
export ANTHROPIC_MODEL="claude-sonnet-4-5"

# 可选：自定义 API 基础 URL（默认 https://api.anthropic.com）
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 基础对话

```python
import os
from claude_memory_sdk import ClaudeMemoryClient

# 设置 API 密钥（也可以通过环境变量设置）
os.environ["ANTHROPIC_API_KEY"] = "xxx"

os.environ["ANTHROPIC_MODEL"] = "claude-sonnet-4-5-20250929"

os.environ["ANTHROPIC_BASE_URL"] = "xxx"
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
    model="claude-sonnet-4-5",  # 指定模型
    max_tokens=4096                     # 自定义令牌限制
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

SDK 的入口类，封装与 Claude API 和记忆工具的交互流程。

#### 初始化参数

| 参数 | 说明 |
| ---- | ---- |
| `api_key` | Anthropic API 密钥，默认读取 `ANTHROPIC_API_KEY` |
| `base_url` | API 基础 URL，默认读取 `ANTHROPIC_BASE_URL` |
| `memory_backend` | 自定义 `BaseMemoryBackend` 实例，默认文件系统后端 |
| `model` | 使用的模型名称，默认 `claude-4-sonnet` 或读取 `ANTHROPIC_MODEL` |
| `max_tokens` | 单次回复的最大 tokens 数，默认为 2048 |
| `context_management` | 上下文清理策略，默认为内置配置（保留记忆工具调用） |
| `memory_system_prompt` | 自定义记忆系统提示词 |
| `auto_save_memory` | 是否在工具调用后执行自动校验/持久化（默认开启） |
| `use_full_schema` | （已弃用）与旧版 SDK 兼容的参数，当前会被忽略 |
| `auto_handle_tool_calls` | 是否在收到 `tool_use` 时递归拉取更多消息（默认关闭） |

#### 对话与上下文

- `chat(user_input: str) -> str`
  - 发送用户输入，内部通过 `tool_runner` 调度记忆工具，并将 Claude 回复追加到历史中。
- `get_conversation_history() -> List[BetaMessageParam]`
  - 返回当前完整消息历史，可用于调试工具事件。
- `clear_conversation_history() -> None`
  - 清空会话历史记录（不会影响已写入的记忆文件）。
- `set_system_prompt(prompt: str) -> None`
  - 替换默认的记忆系统提示词。
- `set_context_management(config: Dict[str, Any]) -> None`
  - 自定义上下文清理策略，覆盖默认配置。
- `get_token_usage_info() -> Optional[Dict[str, Any]]`
  - 返回最近一次 API 调用的 token 统计（若 SDK 提供）。

#### 记忆管理

- `add_memory(path: str, content: str) -> None`
  - 创建或覆盖记忆文件，路径必须位于 `/memories` 下。
- `get_memory(path: str, view_range: Optional[tuple] = None) -> str`
  - 读取文件或目录内容，可选 `view_range=(start, end)` 限定行号。
- `delete_memory(path: str) -> None`
  - 删除指定文件或目录（根目录 `/memories` 会被保护）。
- `clear_all_memories() -> None`
  - 调用当前后端的清空逻辑，重置整个记忆目录。
- `memory_exists(path: str) -> bool`
  - 检查路径是否存在。
- `list_memories(path: str = "/memories") -> List[str]`
  - 返回指定目录下的文件/目录列表。
- `get_memory_stats() -> Dict[str, Any]`
  - 汇总当前记忆目录的文件数、目录数、容量等信息。
- `backup_memory(backup_path: str) -> None`
  - 导出记忆数据为 zip 包。
- `restore_memory(backup_path: str) -> None`
  - 从备份 zip 中恢复记忆。

#### 其他工具

- `interactive_loop() -> None`
  - 内置终端交互演示，支持常见命令。

> 提示：所有写操作都会触发 `auto_save_memory` 钩子，用于校验或扩展持久化策略。

### MemoryBackendTool

`MemoryBackendTool` 继承自官方 `BetaAbstractMemoryTool`，将任何 `BaseMemoryBackend` 实例包装成可注入 `tool_runner` 的工具。默认 `ClaudeMemoryClient` 会实例化该工具并将其传入 API 请求。自定义后端只需实现基类接口即可自动支持记忆工具调用。

### BaseMemoryBackend

抽象基类，约束所有记忆存储后端需实现的最小接口：

- `view(path, view_range=None)`：读取目录或文件（支持行号过滤）。
- `create(path, file_text)`：写入新文件，若父目录不存在需自动创建。
- `str_replace(path, old_str, new_str)`：在文件中进行唯一字符串替换。
- `insert(path, insert_line, insert_text)`：在指定行插入文本。
- `delete(path)`：删除文件或目录。
- `rename(old_path, new_path)`：移动/重命名路径。

可选扩展（如未实现将抛出 `NotImplementedError`）:

- `clear_all_memory()`、`memory_exists()`、`list_memories()`、`get_memory_stats()`、`backup_memory()`、`restore_memory()`。

### FileSystemMemoryBackend

默认实现，使用本地文件系统存储记忆数据，特点：

- 使用 `Path.resolve()` + `relative_to()` 防止目录遍历。
- 忽略隐藏文件，支持递归统计目录。
- `backup_memory` / `restore_memory` 使用 zip 归档便于迁移。
- 所有路径以 `/memories` 为根，自动创建缺失目录。

### 异常层级

- `MemorySDKError`：SDK 顶层异常基类。
- `MemoryBackendError` 及细分的 `MemoryPathError`、`MemoryFileOperationError`：后端相关错误。
- `MemoryAPIError` 及其子类：`MemoryAuthenticationError`、`MemoryRateLimitError`、`MemoryTimeoutError` 等，便于区分 API 失败原因。

开发时捕获这些异常，可以更精细地处理鉴权、限流、文件系统等错误情形。

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

## 🚢 发布指南

1. 更新版本号：修改 `claude_memory_sdk/__version__` 并在 `CHANGELOG.md` 中记录变更。
2. 清理旧的构建产物：
   ```bash
   rm -rf build dist *.egg-info
   ```
3. 构建发布包：
   ```bash
   python -m build
   ```
4. 本地校验生成的包：
   ```bash
   twine check dist/*
   ```
5. 发布到 PyPI：
   ```bash
   twine upload dist/*
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

