# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Memory Lake SDK 项目，旨在为开发者提供简化的 Claude Memory Tool 使用接口。项目包含完整的 Python SDK 实现，支持可插拔的记忆存储后端。

## 常用开发命令

### 环境设置
```powershell
# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 安装开发依赖
pip install -e .[dev]

# 安装 pre-commit 钩子
pre-commit install
```

### 测试命令
```powershell
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=memory_lake_sdk --cov-report=html

# 运行特定测试文件
pytest memory_lake_sdk/tests/test_client.py
pytest memory_lake_sdk/tests/test_memory_backend.py

# 运行特定测试函数
pytest memory_lake_sdk/tests/test_client.py::MemoryLakeClientTest::test_chat
```

### 代码质量检查
```powershell
# 代码格式化
black memory_lake_sdk/

# 导入排序
isort memory_lake_sdk/

# 代码检查
flake8 memory_lake_sdk/

# 类型检查
mypy memory_lake_sdk/

# 安全检查
bandit -r memory_lake_sdk/
safety check
```

### 构建和发布
```powershell
# 构建包
python -m build

# 检查包
twine check dist/*

# 发布到测试 PyPI
twine upload --repository testpypi dist/*

# 发布到正式 PyPI
twine upload dist/*
```

### 示例运行
```powershell
# 运行基础聊天示例
python -m memory_lake_sdk.examples.basic_chat

# 运行记忆管理示例
python -m memory_lake_sdk.examples.manage_memory

# 或使用安装后的命令行工具
claude-memory-chat
claude-memory-manage
```

## 核心架构

### 分层架构设计
1. **SDK Public API** (`client.py`): 用户直接调用的接口层
2. **Core Logic Layer** (`client.py`): 处理对话流程和记忆决策
3. **Anthropic API Client**: 与 Claude API 通信的底层层
4. **Abstract Memory Backend** (`memory_backend.py`): 可插拔存储抽象接口
5. **Concrete Backends**: 具体存储实现（如文件系统）

### 关键组件

#### MemoryLakeClient (`memory_lake_sdk/client.py`)
- 主要客户端类，处理与 Claude API 的交互
- 自动处理记忆工具调用循环
- 支持上下文管理和对话历史
- 核心方法：`chat()`, `add_memory()`, `get_memory()`, `delete_memory()`

#### BaseMemoryBackend (`memory_lake_sdk/memory_backend.py`)
- 抽象基类，定义记忆存储接口
- 强制所有实现包含安全检查
- 抽象方法：`view()`, `create()`, `str_replace()`, `insert()`, `delete()`, `rename()`

#### FileSystemMemoryBackend (`memory_lake_sdk/memory_backend.py`)
- 默认的文件系统存储实现
- 包含严格的路径安全检查（`_get_safe_path()`）
- 防止路径遍历攻击
- 所有路径必须以 `/memories` 开头

### 安全性要点
- **路径验证**: 所有路径操作必须通过 `_get_safe_path()` 验证
- **目录遍历防护**: 防止访问 `/memories` 目录之外的文件
- **数据主权**: 记忆数据存储在用户环境中，SDK 不接触用户数据

## 开发注意事项

### 环境变量配置
- `ANTHROPIC_API_KEY`: 必需的 API 密钥
- `ANTHROPIC_MODEL`: 可选，默认为 "claude-4-sonnet"
- `ANTHROPIC_BASE_URL`: 可选，自定义 API 端点

### 关键依赖
- `anthropic>=0.20.0`: 官方 Anthropic SDK
- 严禁使用 FastAPI 或其他 Web 服务框架
- 必须使用官方 `anthropic` 库作为 HTTP 客户端

### API 配置要求
- 模型：默认使用 `"claude-4-sonnet"`
- 工具：必须包含 `{"type": "memory_20250818", "name": "memory"}`
- Betas：必须包含 `["context-management-2025-06-27"]`

### 测试策略
- 单元测试覆盖所有核心功能
- 集成测试验证 API 交互
- Mock 外部 API 调用
- 安全性测试验证路径检查

### 代码规范
- 使用 Black 进行代码格式化（行长度 88）
- 使用 isort 进行导入排序
- 使用 mypy 进行类型检查（严格模式）
- 使用 flake8 进行代码质量检查
- 所有公共 API 必须包含类型注解和文档字符串

## 项目结构

```
memory_lake_sdk/
├── memory_lake_sdk/
│   ├── __init__.py              # 包初始化和版本信息
│   ├── client.py                # 主客户端类
│   ├── memory_backend.py        # 记忆后端抽象和实现
│   ├── exceptions.py            # 自定义异常类
│   ├── examples/                # 示例代码
│   │   ├── basic_chat.py        # 基础聊天示例
│   │   ├── manage_memory.py     # 记忆管理示例
│   │   └── custom_backend.py    # 自定义后端示例
│   └── tests/                   # 测试文件
│       ├── test_client.py       # 客户端测试
│       └── test_memory_backend.py # 后端测试
├── setup.py                     # 传统安装配置
├── pyproject.toml              # 现代项目配置
├── requirements.txt            # 核心依赖
├── requirements-dev.txt        # 开发依赖
└── README.md                   # 项目文档
```