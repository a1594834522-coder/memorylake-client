#!/usr/bin/env python3
"""
Claude Memory SDK 完整功能示例

本示例展示了如何使用Claude Memory SDK的所有核心功能：
1. 多轮对话
2. 记忆的增删改查
3. 会话管理
4. 高级记忆操作
"""

import sys
import os
from pathlib import Path

# 添加SDK路径
sdk_path = Path(__file__).parent.parent
sys.path.insert(0, str(sdk_path))

from claude_memory_sdk import ClaudeMemoryClient


def basic_conversation_example(client):
    """基础对话示例"""
    print("=== 基础对话示例 ===")

    # 第一次对话 - 建立身份信息
    print("\n用户: 我叫张三，是一名软件工程师，喜欢Python编程")
    response1 = client.ask("我叫张三，是一名软件工程师，喜欢Python编程")
    print(f"Claude: {response1.answer}")
    print(f"会话ID: {response1.session_id}")

    # 第二次对话 - 测试记忆
    print("\n用户: 我的工作是什么？")
    response2 = client.ask("我的工作是什么？")
    print(f"Claude: {response2.answer}")

    # 第三次对话 - 测试偏好记忆
    print("\n用户: 我喜欢什么编程语言？")
    response3 = client.ask("我喜欢什么编程语言？")
    print(f"Claude: {response3.answer}")

    return response2.session_id


def memory_crud_example(client):
    """记忆增删改查示例"""
    print("\n\n=== 记忆增删改查示例 ===")

    # 1. 创建记忆 (Create)
    print("\n1. 创建新记忆")

    # 使用便利方法记住信息
    success = client.remember("教育背景", "北京大学计算机科学与技术专业硕士")
    print(f"记住教育背景: {'成功' if success else '失败'}")

    success = client.remember("技能特长", "精通Python、JavaScript，熟悉机器学习算法")
    print(f"记住技能特长: {'成功' if success else '失败'}")

    # 使用记忆操作创建详细记忆文件
    from claude_memory_sdk.memory_operations import MemoryOperations
    memory_ops = MemoryOperations(client)

    project_content = """
    个人项目经验：
    1. 智能推荐系统 - 使用协同过滤算法，提升推荐精度30%
    2. 数据分析平台 - 处理TB级数据，实现实时可视化
    3. 自动化测试框架 - 提升测试效率80%，减少人工错误
    """

    response = memory_ops.create_memory("/memories/projects.txt", project_content)
    print(f"创建项目记忆文件: {response.message}")

    # 2. 读取记忆 (Read)
    print("\n2. 查看记忆内容")

    # 查看所有记忆文件
    files_list = client.list_memory_files()
    print(f"记忆文件总数: {files_list.total_count}")
    for file_info in files_list.files[:3]:  # 显示前3个文件
        print(f"  - {file_info.name}")

    # 查看特定记忆
    education = client.recall("教育背景")
    print(f"教育背景: {education}")

    skills = client.recall("技能特长")
    print(f"技能特长: {skills}")

    # 查看详细记忆
    project_response = client.view_memory("/memories/projects.txt")
    print(f"项目经验:\n{project_response.contents}")

    # 3. 更新记忆 (Update)
    print("\n3. 更新记忆内容")

    # 追加新的项目经验
    new_project = "4. 微服务架构设计 - 支持日均百万级请求"
    memory_ops.append_memory("/memories/projects.txt", new_project)

    # 更新技能信息
    updated_skills = "精通Python、JavaScript、Go，熟悉机器学习和深度学习算法"
    client.remember("技能特长更新", updated_skills)

    print("已更新项目经验和技能信息")

    # 4. 搜索记忆
    print("\n4. 搜索记忆")

    search_results = memory_ops.search_memories("Python")
    print(f"包含'Python'的记忆:")
    for result in search_results:
        print(f"  文件: {result['file']} (匹配{result['matches']}处)")
        for line in result['lines'][:2]:  # 显示前2个匹配行
            print(f"    行{line['line_number']}: {line['content']}")

    # 5. 删除记忆 (Delete)
    print("\n5. 删除过期记忆")

    # 删除特定的记忆文件
    try:
        delete_response = client.delete_memory_file("/memories/skills.txt")
        print(f"删除技能文件: {delete_response.message}")
    except Exception as e:
        print(f"删除技能文件失败: {e}")


def multi_conversation_management_example(client):
    """多对话管理示例"""
    print("\n\n=== 多对话管理示例 ===")

    from claude_memory_sdk.conversation import ConversationManager

    conversation_manager = ConversationManager()

    # 创建不同主题的对话
    print("\n1. 创建工作主题对话")
    work_conv_id = conversation_manager.create_conversation("工作讨论")
    print(f"工作对话ID: {work_conv_id}")

    print("\n2. 创建学习主题对话")
    study_conv_id = conversation_manager.create_conversation("学习计划")
    print(f"学习对话ID: {study_conv_id}")

    # 在不同对话中添加消息
    print("\n3. 在工作对话中添加消息")
    conversation_manager.add_message_to_current("user", "我需要设计一个新的API系统")
    conversation_manager.add_message_to_current("assistant", "我可以帮你设计RESTful API架构")

    print("\n4. 在学习对话中添加消息")
    conversation_manager.switch_conversation(study_conv_id)
    conversation_manager.add_message_to_current("user", "我想学习深度学习框架")
    conversation_manager.add_message_to_current("assistant", "推荐从PyTorch开始学习")

    # 查看对话统计
    stats = conversation_manager.get_conversation_stats()
    print(f"\n5. 对话统计信息")
    print(f"总对话数: {stats['total_conversations']}")
    print(f"总消息数: {stats['total_messages']}")
    print(f"活跃对话数: {stats['active_conversations']}")

    # 切换回工作对话
    print("\n6. 切换回工作对话")
    work_conv = conversation_manager.switch_conversation(work_conv_id)
    print(f"当前对话: {work_conv.title}")
    last_message = work_conv.get_last_message()
    if last_message:
        print(f"最后消息: {last_message.role}: {last_message.content}")


def advanced_memory_operations_example(client):
    """高级记忆操作示例"""
    print("\n\n=== 高级记忆操作示例 ===")

    from claude_memory_sdk.memory_operations import MemoryOperations
    memory_ops = MemoryOperations(client)

    # 1. 备份记忆
    print("\n1. 备份所有记忆")
    backup_path = memory_ops.backup_memory("./memory_backup.json")
    print(f"记忆已备份到: {backup_path}")

    # 2. 记忆整理
    print("\n2. 整理记忆文件")
    organize_rules = {
        r'.*profile.*': '/memories/personal/',
        r'.*skill.*': '/memories/professional/',
        r'.*project.*': '/memories/work/',
        r'.*note.*': '/memories/notes/',
        r'.*todo.*': '/memories/tasks/'
    }

    organize_result = memory_ops.organize_memories(organize_rules)
    print(f"整理结果: 移动{organize_result['moved']}个文件，失败{organize_result['failed']}个")

    # 3. 记忆摘要
    print("\n3. 生成记忆摘要")
    summary = memory_ops.get_memory_summary()
    print(f"记忆路径: {summary['path']}")
    print(f"文件总数: {summary['total_files']}")
    print(f"总大小: {summary['total_size']}字节")

    # 4. 批量操作
    print("\n4. 批量提问测试")
    questions = [
        "我的职业是什么？",
        "我有什么技能？",
        "我做过什么项目？"
    ]

    responses = client.ask_batch(questions)
    for i, response in enumerate(responses):
        print(f"问题{i+1}: {questions[i]}")
        print(f"回答: {response.answer[:100]}...")


def export_and_analysis_example(client):
    """导出和分析示例"""
    print("\n\n=== 导出和分析示例 ===")

    # 1. 导出为JSON格式
    print("\n1. 导出记忆为JSON格式")
    json_export = client.export_memory("json")
    print(f"JSON导出长度: {len(json_export)}字符")

    # 2. 导出为文本格式
    print("\n2. 导出记忆为文本格式")
    text_export = client.export_memory("text")
    lines = text_export.split('\n')
    print(f"文本导出行数: {len(lines)}")

    # 显示部分导出内容
    print("\n3. 导出内容预览")
    print("前10行内容:")
    for line in lines[:10]:
        print(f"  {line}")


def main():
    """主函数"""
    print("🧠 Claude Memory SDK 完整功能演示")
    print("=" * 50)

    # 创建客户端
    try:
        client = ClaudeMemoryClient("http://localhost:8002")
        print("✅ 客户端连接成功")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("请确保Claude Memory Server正在运行 (python3 main.py)")
        return

    try:
        # 1. 基础对话示例
        session_id = basic_conversation_example(client)

        # 2. 记忆增删改查示例
        memory_crud_example(client)

        # 3. 多对话管理示例
        multi_conversation_management_example(client)

        # 4. 高级记忆操作示例
        advanced_memory_operations_example(client)

        # 5. 导出和分析示例
        export_and_analysis_example(client)

        print("\n\n🎉 所有功能演示完成！")
        print("=" * 50)
        print("您现在已经了解了Claude Memory SDK的主要功能：")
        print("✅ 多轮对话与上下文记忆")
        print("✅ 记忆的增删改查操作")
        print("✅ 高级记忆管理和搜索")
        print("✅ 多对话会话管理")
        print("✅ 数据备份和导出")

    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        client.close()
        print("\n🔚 客户端连接已关闭")


if __name__ == "__main__":
    main()