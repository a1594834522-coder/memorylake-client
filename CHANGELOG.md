# 更新日志

本文档记录了 Memory Lake SDK 的所有重要更改。

## [0.3.0] - 2025-01-14

### 重大更新
- 🔁 将核心命名从 `ClaudeMemoryClient` 重构为 `MemoryLakeClient`，与 PyPI 包 `memory-lake-sdk` 品牌保持一致
- 📦 同步更新包名、入口脚本与清单配置，统一使用 `memory_lake_sdk` 命名空间
- 📚 更新 README、示例与开发文档，覆盖新的导入路径与用法

---

## [0.2.0] - 2025-01-13

### 新增
- 📄 新增 MIT `LICENSE`、`MANIFEST.in` 等发布所需文件
- 🛠️ 提供 `memory_lake_sdk.examples.manage_memory` 与 `custom_backend` 示例脚本
- 📦 `memory_lake_sdk.examples` 现作为正式子包发布，并附带示例文档
- 🧰 README 新增 PyPI 发布流程说明
- 🔁 PyPI 发布包更名为 `memory-lake-sdk`

### 变更
- ⬆️ 将 `anthropic` 最低版本提升至 `0.39.0` 以匹配最新 Memory Tool API
- 🔧 调整打包配置以包含示例资源与许可证信息
- 📝 更新 `setup.py`、`pyproject.toml`、`requirements.txt` 以支持 PyPI 上传
- 🌐 示例与文档默认使用官方 `https://api.anthropic.com` 端点，并移除占位 API Key

---

## [0.1.0] - 2025-10-11

### 新增
- 🎉 初始版本发布
- ✨ 完整的 Claude Memory Tool SDK 实现
- 🧠 智能记忆管理功能
- 🔌 可插拔存储后端系统
- 🛡️ 安全路径验证和遍历防护
- 📦 PyPI 包配置和构建支持

### 核心功能
- **MemoryLakeClient**: 主客户端类，提供对话和记忆管理
- **BaseMemoryBackend**: 抽象基类，支持自定义存储后端
- **FileSystemMemoryBackend**: 默认文件系统存储实现
- **完整异常体系**: 包含各种错误处理类型

### 环境变量支持
- `ANTHROPIC_API_KEY`: API 密钥配置（必需）
- `ANTHROPIC_MODEL`: 模型选择（可选，默认 claude-4-sonnet）
- `ANTHROPIC_BASE_URL`: 自定义 API 端点（可选）

### API 功能
- `chat(user_input)`: 智能对话，自动处理记忆工具调用
- `add_memory(path, content)`: 添加记忆文件
- `get_memory(path, view_range)`: 读取记忆内容
- `delete_memory(path)`: 删除记忆文件
- `clear_all_memories()`: 清除所有记忆

### 示例和文档
- 📚 完整的 README.md 文档
- 💡 三个实用示例：
  - `basic_chat.py`: 基础聊天示例
  - `manage_memory.py`: 记忆管理示例
  - `custom_backend.py`: 自定义后端示例
- 🧪 全面的单元测试覆盖

### 安全特性
- 🔒 严格的路径验证（必须以 `/memories` 开头）
- 🛡️ 防止目录遍历攻击
- 📁 路径解析和安全检查
- ⚠️ 权限控制限制

### 开发工具
- 🔧 完整的开发环境配置
- 📋 测试套件和覆盖率报告
- 🎨 代码格式化和质量检查工具
- 📦 自动化构建和打包配置

### 配置文件
- `setup.py`: 传统安装配置
- `pyproject.toml`: 现代项目配置
- `requirements.txt`: 生产依赖
- `requirements-dev.txt`: 开发依赖
- `.env.example`: 环境变量配置示例

---

## 版本说明

### 版本号格式
本项目使用 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 支持的 Python 版本
- Python 3.8+
- Python 3.9+
- Python 3.10+
- Python 3.11+
- Python 3.12+

### 支持的 Claude 模型
- `claude-4-sonnet` (默认)
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

---

## 贡献指南

欢迎贡献代码！请查看 README.md 中的贡献指南部分。

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。
