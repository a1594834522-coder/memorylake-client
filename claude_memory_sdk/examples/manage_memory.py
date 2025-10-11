#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管理示例

演示如何使用 Claude Memory SDK 进行记忆管理操作。
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入claude_memory_sdk
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_memory_sdk import ClaudeMemoryClient


def main():
    """主函数 - 记忆管理示例"""
    print("=== Claude Memory SDK 记忆管理示例 ===\n")

    # 设置环境变量
    os.environ.setdefault('ANTHROPIC_API_KEY', 'your-api-key-here')

    try:
        # 初始化客户端
        print("1. 初始化客户端...")
        client = ClaudeMemoryClient()
        print("[OK] 客户端初始化成功\n")

        # 创建各种类型的记忆
        print("2. 创建记忆文件...")

        # 用户档案
        client.add_memory("/memories/profile.txt",
            "用户档案:\n"
            "姓名: 张三\n"
            "职业: 软件工程师\n"
            "技能: Python, JavaScript, 机器学习\n"
            "兴趣: 开源项目, 技术写作"
        )

        # 项目信息
        client.add_memory("/memories/projects/current_project.txt",
            "当前项目: Claude Memory SDK\n"
            "描述: 开发一个易用的Claude记忆工具SDK\n"
            "状态: 开发中\n"
            "技术栈: Python, Anthropic API"
        )

        # 学习笔记
        client.add_memory("/memories/notes/python_tips.txt",
            "Python编程技巧:\n"
            "1. 使用列表推导式简化代码\n"
            "2. 善用上下文管理器处理资源\n"
            "3. 使用f-string进行字符串格式化\n"
            "4. 掌握装饰器的使用"
        )

        # 会议记录
        client.add_memory("/memories/meetings/2024-10-11_team_sync.txt",
            "团队同步会议 - 2024年10月11日\n"
            "参会者: 开发团队全体成员\n"
            "讨论主题:\n"
            "- SDK功能测试结果\n"
            "- 下一步开发计划\n"
            "- 文档编写任务分配"
        )

        print("[OK] 记忆文件创建成功")

        # 列出所有记忆
        print("\n3. 列出所有记忆...")
        memories = client.list_memories()
        print(f"总共 {len(memories)} 个记忆项目:")
        for memory in memories:
            print(f"  - {memory}")

        # 读取特定记忆
        print("\n4. 读取用户档案...")
        profile = client.get_memory("/memories/profile.txt")
        print("用户档案内容:")
        print(profile)

        # 读取特定行范围
        print("\n5. 读取学习笔记的前3行...")
        tips_partial = client.get_memory("/memories/notes/python_tips.txt", (1, 3))
        print("Python技巧 (前3行):")
        print(tips_partial)

        # 检查记忆是否存在
        print("\n6. 检查记忆文件存在性...")
        test_files = [
            "/memories/profile.txt",
            "/memories/nonexistent.txt",
            "/memories/projects/"
        ]

        for file_path in test_files:
            exists = client.memory_exists(file_path)
            print(f"  {file_path}: {'存在' if exists else '不存在'}")

        # 获取统计信息
        print("\n7. 获取记忆统计信息...")
        stats = client.get_memory_stats()
        print("记忆存储统计:")
        print(f"  - 总文件数: {stats['total_files']}")
        print(f"  - 总目录数: {stats['total_directories']}")
        print(f"  - 总大小: {stats['total_size_bytes']} 字节")
        print(f"  - 最大文件: {stats['largest_file']}")
        print(f"  - 文件类型分布: {stats['file_types']}")

        # 备份记忆
        print("\n8. 备份记忆数据...")
        backup_path = "memory_backup_example.zip"
        client.backup_memory(backup_path)
        print(f"[OK] 备份完成: {backup_path}")

        # 演示记忆更新
        print("\n9. 更新记忆内容...")
        client.add_memory("/memories/profile.txt",
            "用户档案 (更新版):\n"
            "姓名: 张三\n"
            "职业: 高级软件工程师\n"  # 职业升级
            "技能: Python, JavaScript, 机器学习, Go\n"  # 新增Go技能
            "兴趣: 开源项目, 技术写作, 系统设计\n"  # 新增系统设计
            "更新时间: 2024-10-11"
        )
        print("[OK] 用户档案已更新")

        # 演示删除记忆
        print("\n10. 删除特定记忆...")
        client.delete_memory("/memories/meetings/2024-10-11_team_sync.txt")
        print("[OK] 会议记录已删除")

        # 再次列出记忆，确认删除
        final_memories = client.list_memories()
        print(f"\n删除后剩余记忆数: {len(final_memories)}")

        # 恢复记忆
        print("\n11. 从备份恢复记忆...")
        client.clear_all_memories()
        print("[OK] 所有记忆已清除")

        client.restore_memory(backup_path)
        print("[OK] 从备份恢复记忆成功")

        restored_memories = client.list_memories()
        print(f"恢复后记忆数: {len(restored_memories)}")

        print("\n=== 记忆管理示例完成 ===")
        print("所有功能演示成功!")

        return True

    except Exception as e:
        print(f"[ERROR] 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)