#!/usr/bin/env python3
"""
Claude Memory SDK 基础使用示例
"""

import sys
import os

# 添加父目录到路径以便导入SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from claude_memory_sdk import ClaudeMemoryClient


def main():
    """基础使用示例"""
    print("🧠 Claude Memory SDK 基础使用示例")
    print("=" * 50)

    # 创建客户端
    client = ClaudeMemoryClient("http://localhost:8002")

    try:
        # 1. 检查API状态
        print("\n1. 检查API状态...")
        api_info = client.get_api_info()
        print(f"✅ API版本: {api_info.version}")
        print(f"✅ API状态: {api_info.status}")

        # 2. 首次对话
        print("\n2. 首次对话...")
        response1 = client.ask("我叫张三，喜欢编程，正在学习Python")
        print(f"🤖 Claude: {response1.answer}")
        print(f"🆔 会话ID: {response1.session_id}")
        print(f"📁 记忆文件: {response1.memory_files}")

        # 3. 续会话测试记忆功能
        print("\n3. 测试记忆功能...")
        response2 = client.ask("我的名字是什么？我喜欢什么？")
        print(f"🤖 Claude: {response2.answer}")
        print(f"📁 新增记忆文件: {response2.memory_files}")

        # 4. 查看记忆内容
        print("\n4. 查看记忆内容...")
        memory_response = client.view_memory("/memories")
        print("📁 记忆目录内容:")
        print(memory_response.contents)

        # 5. 查看所有记忆文件
        print("\n5. 查看所有记忆文件...")
        files_response = client.list_memory_files()
        print(f"📄 找到 {files_response.total_count} 个记忆文件:")
        for file_info in files_response.files:
            print(f"  - {file_info.name} ({file_info.size} bytes)")

        # 6. 创建自定义记忆文件
        print("\n6. 创建自定义记忆文件...")
        create_response = client.create_memory_file(
            "/memories/personal_notes.txt",
            "这是一个个人笔记文件\n包含重要信息和学习进度"
        )
        print(f"✅ {create_response.message}")

        # 7. 获取会话信息
        print("\n7. 获取会话信息...")
        session_info = client.get_session_info()
        print(f"🆔 会话ID: {session_info.session_id}")
        print(f"💬 消息数量: {session_info.message_count}")
        print(f"📁 关联文件: {', '.join(session_info.memory_files)}")

        # 8. 导出记忆内容
        print("\n8. 导出记忆内容...")
        memory_export = client.export_memory("text")
        print("📄 记忆内容导出:")
        print(memory_export[:200] + "..." if len(memory_export) > 200 else memory_export)

        print("\n✅ 示例运行完成！")

    except Exception as e:
        print(f"❌ 运行出错: {e}")
        print("请确保Claude Memory服务器正在运行 (http://localhost:8002)")


if __name__ == "__main__":
    main()