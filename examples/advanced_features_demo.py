#!/usr/bin/env python3
"""
Claude Memory 高级功能演示

展示新的统一会话管理和高级记忆功能
"""

import sys
import os

# 添加SDK路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'claude-memory-sdk'))

from claude_memory_sdk import (
    ClaudeMemoryClient,
    MemorySearchRequest,
    MemoryBackupRequest,
    MemoryOrganizeRequest
)


def demo_unified_session_management():
    """演示统一会话管理功能"""
    print("🔧 === 统一会话管理演示 ===")

    client = ClaudeMemoryClient()

    # 1. 创建新会话
    print("\n1. 创建新会话...")
    response1 = client.ask("你好，我叫张三，是一名软件工程师")
    print(f"   会话ID: {response1.session_id}")
    print(f"   回答: {response1.answer}")

    # 2. 继续对话
    print("\n2. 继续对话...")
    response2 = client.ask("我的职业是什么？")
    print(f"   回答: {response2.answer}")

    # 3. 获取会话信息
    print("\n3. 获取会话信息...")
    session_info = client.get_session_info()
    print(f"   会话ID: {session_info.session_id}")
    print(f"   消息数量: {session_info.message_count}")
    print(f"   创建时间: {session_info.created_at}")
    print(f"   最后活动: {session_info.last_activity}")

    # 4. 列出所有会话
    print("\n4. 列出所有活跃会话...")
    sessions = client.list_sessions()
    print(f"   总会话数: {sessions.total}")
    for session in sessions.sessions:
        print(f"   - {session.session_id}: {session.message_count} 条消息")

    # 5. 清除会话历史
    print("\n5. 清除会话历史...")
    result = client.clear_session()
    print(f"   结果: {result}")

    print("\n✅ 统一会话管理演示完成\n")


def demo_memory_search():
    """演示记忆搜索功能"""
    print("🔍 === 记忆搜索演示 ===")

    client = ClaudeMemoryClient()

    # 先创建一些测试记忆
    print("\n1. 创建测试记忆...")
    client.create_memory_file("/memories/profile.txt", "姓名：张三\n职业：软件工程师\n爱好：Python编程")
    client.create_memory_file("/memories/projects.txt", "项目1：AI聊天系统\n项目2：数据分析平台\n技术栈：Python, FastAPI")
    client.create_memory_file("/memories/notes.txt", "今天学习了Python的高级特性\n明天要学习FastAPI框架")

    # 2. 搜索包含"Python"的记忆
    print("\n2. 搜索包含'Python'的记忆...")
    search_result = client.search_memory("Python")
    print(f"   总匹配数: {search_result.total_matches}")

    for result in search_result.results:
        print(f"   文件: {result.file}")
        print(f"   匹配数: {result.match_count}")
        for match in result.matches:
            print(f"     第{match['line_number']}行: {match['content']}")
        print()

    # 3. 在特定文件类型中搜索
    print("\n3. 在.txt文件中搜索'项目'...")
    search_result = client.search_memory("项目", "*.txt")
    print(f"   总匹配数: {search_result.total_matches}")

    for result in search_result.results:
        print(f"   文件: {result.file}")
        for match in result.matches:
            print(f"     {match['content']}")

    print("\n✅ 记忆搜索演示完成\n")


def demo_memory_backup():
    """演示记忆备份功能"""
    print("💾 === 记忆备份演示 ===")

    client = ClaudeMemoryClient()

    # 1. JSON格式备份
    print("\n1. 创建JSON格式备份...")
    backup_response = client.backup_memory("json")
    print(f"   消息: {backup_response.message}")
    if backup_response.backup_data:
        # 只显示备份的前100个字符
        preview = backup_response.backup_data[:100] + "..." if len(backup_response.backup_data) > 100 else backup_response.backup_data
        print(f"   备份数据预览: {preview}")

    # 2. ZIP格式备份（如果支持）
    print("\n2. 创建ZIP格式备份...")
    backup_response = client.backup_memory("zip")
    print(f"   消息: {backup_response.message}")
    if backup_response.download_url:
        print(f"   下载链接: {backup_response.download_url}")

    print("\n✅ 记忆备份演示完成\n")


def demo_memory_organize():
    """演示记忆整理功能"""
    print("📁 === 记忆整理演示 ===")

    client = ClaudeMemoryClient()

    # 创建一些需要整理的文件
    print("\n1. 创建测试文件...")
    client.create_memory_file("/memories/user_profile.txt", "用户档案信息")
    client.create_memory_file("/memories/personal_notes.txt", "个人笔记")
    client.create_memory_file("/memories/project_plan.txt", "项目计划")
    client.create_memory_file("/memories/work_tasks.txt", "工作任务")

    # 2. 预览整理
    print("\n2. 预览整理...")
    rules = {
        r".*profile.*": "/memories/personal/",
        r".*personal.*": "/memories/personal/",
        r".*project.*": "/memories/work/",
        r".*work.*": "/memories/work/"
    }

    organize_response = client.organize_memory(rules, dry_run=True)
    print(f"   消息: {organize_response.message}")
    for move in organize_response.moved_files:
        print(f"   将移动: {move}")

    # 3. 实际整理（注释掉以避免实际移动文件）
    # print("\n3. 执行实际整理...")
    # organize_response = client.organize_memory(rules, dry_run=False)
    # print(f"   消息: {organize_response.message}")
    # for move in organize_response.moved_files:
    #     print(f"   已移动: {move}")

    print("\n✅ 记忆整理演示完成\n")


def demo_batch_operations():
    """演示批量操作功能"""
    print("📦 === 批量操作演示 ===")

    client = ClaudeMemoryClient()

    # 1. 批量提问
    print("\n1. 批量提问...")
    questions = [
        "我叫什么名字？",
        "我的职业是什么？",
        "我喜欢什么？"
    ]

    responses = client.ask_batch(questions)
    for i, response in enumerate(responses):
        print(f"   问题{i+1}: {questions[i]}")
        print(f"   回答{i+1}: {response.answer[:50]}...")
        print()

    print("\n✅ 批量操作演示完成\n")


def main():
    """主演示函数"""
    print("🚀 Claude Memory 高级功能演示")
    print("=" * 50)

    try:
        # 演示各项功能
        demo_unified_session_management()
        demo_memory_search()
        demo_memory_backup()
        demo_memory_organize()
        demo_batch_operations()

        print("🎉 所有演示完成！")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("请确保服务器正在运行 (python claude-memory-server/main.py)")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())