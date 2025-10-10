# Claude Memory SDK

🧠 Claude Memory Q&A API 的官方Python客户端SDK

[![PyPI version](https://badge.fury.io/py/claude-memory-sdk.svg)](https://badge.fury.io/py/claude-memory-sdk)
[![Python versions](https://img.shields.io/pypi/pyversions/claude-memory-sdk.svg)](https://pypi.org/project/claude-memory-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Claude Memory SDK 是一个功能强大的Python客户端库，用于与Claude Memory Q&A API交互。它提供了简单易用的接口来利用Claude的智能记忆功能，让AI能够在对话中记住和管理用户信息。

## ✨ 主要特性

- 🧠 **智能记忆**: Claude自动识别并存储重要信息
- 💾 **持久化存储**: 跨会话的持久化记忆能力
- 🔄 **多轮对话**: 支持复杂的对话流管理
- 📝 **记忆CRUD**: 完整的记忆增删改查操作
- 🎯 **高级搜索**: 基于关键词的记忆搜索功能
- 📊 **批量操作**: 支持批量提问和记忆操作
- 🔄 **会话管理**: 完整的会话生命周期管理
- 🛠️ **类型安全**: 基于Pydantic的完整类型支持
- 🚨 **错误处理**: 完善的异常处理和重试机制
- 📦 **数据管理**: 备份、恢复、整理记忆功能
- 🔧 **高度可配置**: 灵活的配置选项

## 🚀 快速开始

### 安装

```bash
pip install claude-memory-sdk
```

### 基础使用

```python
from claude_memory_sdk import ClaudeMemoryClient

# 创建客户端
client = ClaudeMemoryClient("http://localhost:8002")

# 首次对话 - Claude会记住你的信息
response = client.ask("我叫张三，喜欢编程，正在学习Python")
print(response.answer)  # Claude的回答
print(response.session_id)  # 会话ID

# 续会话 - Claude会记住之前的信息
response = client.ask("我的名字是什么？")
print(response.answer)  # 输出: 你的名字是张三
```

### 上下文管理器使用

```python
from claude_memory_sdk import ClaudeMemoryClient

with ClaudeMemoryClient("http://localhost:8002") as client:
    # 自动管理连接
    response1 = client.ask("我叫李四，是一名前端开发者")
    response2 = client.ask("我的职业是什么？")
    print(response2.answer)  # 会记住职业信息
```

## 📚 详细功能

### 多轮对话和会话管理

```python
# 基础多轮对话
response1 = client.ask("我叫张三，是一名软件工程师")
print(response1.answer)

response2 = client.ask("我的职业是什么？")
print(response2.answer)  # 会记住你是软件工程师

# 高级对话管理
from claude_memory_sdk.conversation import ConversationManager

conv_manager = ConversationManager()

# 创建不同主题的对话
work_conv_id = conv_manager.create_conversation("工作讨论")
study_conv_id = conv_manager.create_conversation("学习计划")

# 在工作对话中添加消息
conv_manager.switch_conversation(work_conv_id)
conv_manager.add_message_to_current("user", "我需要设计一个新系统")
conv_manager.add_message_to_current("assistant", "我可以帮你设计架构")

# 查看对话统计
stats = conv_manager.get_conversation_stats()
print(f"总对话数: {stats['total_conversations']}")
```

### 记忆CRUD操作

```python
# 创建记忆 (Create)
client.remember("教育背景", "北京大学计算机硕士")
client.create_memory_file("/memories/projects.txt", "项目经验详情")

# 读取记忆 (Read)
education = client.recall("教育背景")
projects = client.view_memory("/memories/projects.txt")

# 更新记忆 (Update)
from claude_memory_sdk.memory_operations import MemoryOperations
memory_ops = MemoryOperations(client)

# 追加内容
memory_ops.append_memory("/memories/projects.txt", "新项目经验")

# 替换内容
memory_ops.update_memory("/memories/profile.txt", "更新的个人信息", overwrite=True)

# 删除记忆 (Delete)
client.delete_memory_file("/memories/old_notes.txt")
memory_ops.delete_memory("/memories/temp.txt")
```

### 高级记忆操作

```python
from claude_memory_sdk.memory_operations import MemoryOperations

memory_ops = MemoryOperations(client)

# 搜索记忆
search_results = memory_ops.search_memories("Python")
for result in search_results:
    print(f"文件: {result['file']}, 匹配: {result['matches']}次")

# 备份记忆
backup_path = memory_ops.backup_memory("./memory_backup.json")
print(f"备份保存到: {backup_path}")

# 整理记忆文件
organize_rules = {
    r'.*profile.*': '/memories/personal/',
    r'.*project.*': '/memories/work/',
    r'.*note.*': '/memories/notes/'
}
result = memory_ops.organize_memories(organize_rules)
print(f"整理完成: 移动{result['moved']}个文件")

# 获取记忆摘要
summary = memory_ops.get_memory_summary()
print(f"记忆统计: {summary['total_files']}个文件, {summary['total_size']}字节")
```

### 会话管理

```python
# 获取会话信息
session_info = client.get_session_info()
print(f"会话ID: {session_info.session_id}")
print(f"消息数量: {session_info.message_count}")
print(f"记忆文件: {session_info.memory_files}")

# 清除会话历史
client.clear_session()

# 开始新会话
new_session_id = client.start_new_session()
```

### 便利方法

```python
# 简化的聊天接口
answer = client.chat("今天天气怎么样？")
print(answer)

# 快速记忆操作
client.remember("user_preference", "喜欢简洁的代码风格")
preference = client.recall("user_preference")
print(f"用户偏好: {preference}")

# 批量提问
questions = [
    "我的名字是什么？",
    "我喜欢什么？",
    "我在做什么项目？"
]
responses = client.ask_batch(questions)
for response in responses:
    print(f"回答: {response.answer}")

# 导出记忆数据
memory_json = client.export_memory("json")  # JSON格式
memory_text = client.export_memory("text")  # 文本格式
```

### 高级功能

```python
# 导出记忆内容
memory_json = client.export_memory("json")
memory_text = client.export_memory("text")

# 自定义配置
from claude_memory_sdk import ClaudeMemoryClient, ClientConfig

config = ClientConfig(
    base_url="http://your-api-server:8002",
    timeout=60,
    max_retries=5,
    headers={"User-Agent": "MyApp/1.0"}
)

client = ClaudeMemoryClient(config=config)
```

## 🔧 配置选项

### 基础配置

```python
from claude_memory_sdk import ClaudeMemoryClient

client = ClaudeMemoryClient(
    base_url="http://localhost:8002",  # API服务器地址
    timeout=30,                          # 请求超时时间（秒）
    max_retries=3,                       # 最大重试次数
    retry_delay=1.0,                     # 重试延迟（秒）
    headers={"User-Agent": "MyApp"}      # 自定义请求头
)
```

### 配置对象

```python
from claude_memory_sdk import ClaudeMemoryClient, ClientConfig

config = ClientConfig(
    base_url="http://localhost:8002",
    timeout=30,
    max_retries=3,
    retry_delay=1.0,
    headers={
        "User-Agent": "ClaudeMemorySDK/1.0.0",
        "X-Custom-Header": "value"
    }
)

client = ClaudeMemoryClient(config=config)
```

## 🚨 错误处理

SDK提供了完整的异常处理体系：

```python
from claude_memory_sdk import (
    ClaudeMemoryClient,
    APIError,
    SessionError,
    MemoryError,
    NetworkError,
    TimeoutError
)

client = ClaudeMemoryClient()

try:
    response = client.ask("你好")
except APIError as e:
    print(f"API错误: {e.message} (状态码: {e.status_code})")
except SessionError as e:
    print(f"会话错误: {e.message}")
except MemoryError as e:
    print(f"记忆操作错误: {e.message}")
except NetworkError as e:
    print(f"网络错误: {e.message}")
except TimeoutError as e:
    print(f"请求超时: {e.message}")
```

## 📊 数据模型

SDK使用Pydantic模型确保类型安全：

```python
from claude_memory_sdk import (
    QuestionRequest,
    QuestionResponse,
    MemoryViewRequest,
    SessionInfo
)

# 创建请求对象
request = QuestionRequest(
    question="你好，我是新用户",
    session_id=None  # 可选
)

# 响应对象
response = QuestionResponse(
    answer="你好！很高兴认识你！",
    session_id="session_123456",
    memory_files=["user_profile.xml"],
    timestamp=datetime.now()
)
```

## 🔌 环境变量

可以通过环境变量配置默认值：

```bash
export CLAUDE_MEMORY_BASE_URL="http://localhost:8002"
export CLAUDE_MEMORY_TIMEOUT="30"
export CLAUDE_MEMORY_MAX_RETRIES="3"
```

## 🧪 测试和示例

### 运行测试

SDK提供了完整的测试套件：

```bash
# 运行功能测试
python examples/test_functionality.py

# 运行完整演示
python examples/complete_example.py
```

### 快速测试脚本

```python
from claude_memory_sdk import ClaudeMemoryClient

def quick_test():
    """快速功能测试"""
    client = ClaudeMemoryClient("http://localhost:8002")

    # 测试连接
    api_info = client.get_api_info()
    print(f"✅ 连接成功: {api_info.message}")

    # 测试对话
    response = client.ask("你好，我是测试用户")
    print(f"✅ 对话成功: {response.answer[:50]}...")

    # 测试记忆
    client.remember("测试键", "测试值")
    recalled = client.recall("测试键")
    print(f"✅ 记忆功能: {recalled}")

    print("🎉 所有基础功能正常！")

if __name__ == "__main__":
    quick_test()
```

## 📈 性能优化

### 连接复用

```python
# 使用上下文管理器自动管理连接
with ClaudeMemoryClient() as client:
    # 在这里执行多个操作，会复用连接
    for i in range(10):
        response = client.ask(f"问题 {i}")
        print(response.answer)
```

### 批量操作

```python
# 批量提问比单独调用更高效
questions = [f"问题 {i}" for i in range(10)]
responses = client.ask_batch(questions)
```

## 🔍 故障排除

### 常见问题

1. **连接超时**
   ```python
   client = ClaudeMemoryClient(timeout=60)  # 增加超时时间
   ```

2. **网络错误**
   ```python
   client = ClaudeMemoryClient(
       max_retries=5,  # 增加重试次数
       retry_delay=2.0  # 增加重试延迟
   )
   ```

3. **会话丢失**
   ```python
   # 检查会话是否有效
   try:
       session_info = client.get_session_info()
   except SessionError:
       # 开始新会话
       client.start_new_session()
   ```

### 调试模式

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

client = ClaudeMemoryClient()
response = client.ask("测试消息")
```

## 🔗 相关链接

- 📖 [完整API文档](https://claude-memory-sdk.readthedocs.io/)
- 🐛 [问题反馈](https://github.com/example/claude-memory-sdk/issues)
- 📧 [邮件支持](mailto:support@example.com)
- 🏠 [项目主页](https://github.com/example/claude-memory-sdk)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

*Claude Memory SDK - 让AI拥有记忆能力*