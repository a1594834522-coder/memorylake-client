# Claude Memory SDK 示例

本目录包含了 Claude Memory SDK 的各种使用示例，帮助开发者快速上手。

## 示例文件列表

### 1. basic_chat.py - 基础聊天示例
演示如何使用 Claude Memory SDK 进行交互式对话功能。

**功能演示：**
- 客户端初始化
- 交互式对话模式
- 智能记忆存储（当用户包含关键词时自动保存）
- 对话管理和统计
- 记忆查看和管理

**交互命令：**
- `help` - 显示帮助信息
- `quit/exit` - 退出程序
- `clear` - 清除对话历史
- `stats` - 显示记忆统计
- `memories` - 查看记忆内容
- 直接输入消息与Claude对话

**自动记忆功能：**
当用户输入包含"记住"、"存储"、"保存"、"我的信息"等关键词时，系统会自动将对话内容保存到记忆中。

**运行方式：**
```bash
python claude_memory_sdk/examples/basic_chat.py
```

### 2. manage_memory.py - 记忆管理示例
全面演示记忆管理功能，包括创建、读取、更新、删除记忆等操作。

**功能演示：**
- 创建各种类型的记忆文件
- 列出和查看记忆内容
- 记忆内容更新和删除
- 记忆统计信息
- 备份和恢复功能

**运行方式：**
```bash
python claude_memory_sdk/examples/manage_memory.py
```

### 3. custom_backend.py - 自定义后端示例
演示如何创建自定义的记忆存储后端。

**功能演示：**
- 实现 `InMemoryBackend` 内存后端
- 自定义后端的完整功能
- 备份和恢复机制
- 与客户端的集成

**运行方式：**
```bash
python claude_memory_sdk/examples/custom_backend.py
```

## 使用前准备

### 1. 环境变量设置
在运行示例之前，请确保设置以下环境变量：

```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "your-api-key-here"
$env:ANTHROPIC_BASE_URL = "https://api.anthropic.com"  # 可选，默认即为此值
$env:ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

# Windows (CMD)
set ANTHROPIC_API_KEY=your-api-key-here
set ANTHROPIC_BASE_URL=https://api.anthropic.com
set ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Linux/Mac
export ANTHROPIC_API_KEY="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
```

### 2. 依赖安装
确保已安装所需的依赖包：

```bash
pip install anthropic
```

### 3. 项目路径
示例文件已经配置好了正确的导入路径，可以直接运行。

## 功能特点

### 记忆存储
- 支持文本内容的存储和检索
- 目录结构组织
- 行范围查看功能

### 记忆管理
- 创建、读取、更新、删除（CRUD）操作
- 批量操作支持
- 存在性检查

### 数据安全
- 路径安全验证，防止目录遍历攻击
- 备份和恢复机制
- 错误处理和异常管理

### 统计信息
- 文件数量统计
- 存储大小统计
- 文件类型分析

### 扩展性
- 可插拔的后端架构
- 自定义后端实现
- 标准化接口设计

## 常见问题

### Q: 为什么有些示例中的对话功能不使用记忆工具？
A: 请确保使用官方端点 `https://api.anthropic.com` 并启用最新模型版本。旧的或第三方兼容端点可能不支持 Memory Tool，因此示例会退化为基础对话功能。

### Q: 如何创建自己的记忆后端？
A: 参考 `custom_backend.py` 示例，继承 `BaseMemoryBackend` 类并实现所有抽象方法。

### Q: 记忆数据存储在哪里？
A: 默认使用文件系统后端，数据存储在当前目录的 `memory/` 文件夹中。您可以通过自定义后端来改变存储位置。

### Q: 如何处理中文内容？
A: SDK完全支持UTF-8编码，可以正确处理中文和其他Unicode字符。

## 更多资源

- [项目README](../../README.md)
- [开发文档](../../CLAUDE.md)
- [API参考文档](../../官方SDK参考.md)

## 贡献

欢迎提交问题报告和功能请求！如果您有改进建议或发现了bug，请在项目的GitHub仓库中创建issue。
