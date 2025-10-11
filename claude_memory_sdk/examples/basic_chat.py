#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础聊天示例

演示如何使用 Claude Memory SDK 进行基础对话功能。
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入claude_memory_sdk
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_memory_sdk import ClaudeMemoryClient


def main():
    """主函数 - 基础聊天示例"""
    print("=== Claude Memory SDK 基础聊天示例 ===\n")

    # 设置环境变量（可选，也可以通过环境变量设置）
    os.environ.setdefault('ANTHROPIC_API_KEY', 'de4751f251a8486bb38dde538c20f3c6.Fmd1Nm0X5wvjVVhe')
    os.environ.setdefault('ANTHROPIC_BASE_URL', 'https://open.bigmodel.cn/api/anthropic')
    os.environ.setdefault('ANTHROPIC_MODEL', 'GLM-4.6')

    try:
        # 初始化客户端（自动创建文件系统记忆后台）
        print("正在初始化 Claude Memory 客户端...")
        print("- 记忆后台：文件系统（默认存储在 ./memory/ 目录）")
        client = ClaudeMemoryClient()
        print("[OK] 客户端初始化成功")
        print("- 记忆系统提示词已加载")
        print("- Memory Tool 已配置完成\n")

        # 交互式对话模式
        print("=== 交互式对话模式 ===")
        print("输入消息与Claude对话，输入 'quit' 或 'exit' 退出")
        print("输入 'help' 查看可用命令")
        print("注意：Claude会自动管理记忆，存储重要信息\n")

        conversation_count = 0

        while True:
            try:
                user_input = input("\n您: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("再见!")
                    break

                if user_input.lower() == 'help':
                    print("\n可用命令:")
                    print("  help - 显示此帮助信息")
                    print("  quit/exit - 退出程序")
                    print("  clear - 清除对话历史")
                    print("  stats - 显示记忆统计")
                    print("  memories - 查看记忆内容")
                    print("  memory_add <path> <content> - 手动添加记忆")
                    print("  直接输入消息与Claude对话（Claude会自动管理记忆）")
                    continue

                if user_input.lower() == 'clear':
                    client.clear_conversation_history()
                    print("对话历史已清除!")
                    conversation_count = 0
                    continue

                if user_input.lower() == 'stats':
                    try:
                        stats = client.get_memory_stats()
                        print(f"\n记忆统计:")
                        print(f"  文件数: {stats['total_files']}")
                        print(f"  总大小: {stats['total_size_bytes']} 字节")
                        print(f"  对话轮数: {conversation_count}")
                    except Exception as e:
                        print(f"[ERROR] 获取统计失败: {e}")
                    continue

                if user_input.lower().startswith('memory_add '):
                    # 手动添加记忆命令
                    try:
                        parts = user_input[11:].strip().split(' ', 1)
                        if len(parts) == 2:
                            path, content = parts
                            client.add_memory(path, content)
                            print(f"[OK] 记忆已添加: {path}")
                        else:
                            print("[ERROR] 格式错误，使用: memory_add <path> <content>")
                    except Exception as e:
                        print(f"[ERROR] 添加记忆失败: {e}")
                    continue

                if user_input.lower() == 'memories':
                    try:
                        memories = client.list_memories()
                        if memories:
                            print(f"\n记忆内容 ({len(memories)} 个):")
                            for memory in memories[:10]:  # 只显示前10个
                                print(f"  - {memory}")
                            if len(memories) > 10:
                                print(f"  ... 还有 {len(memories) - 10} 个记忆")
                        else:
                            print("\n暂无记忆内容")
                    except Exception as e:
                        print(f"[ERROR] 获取记忆失败: {e}")
                    continue

                if not user_input:
                    continue

                print("Claude: ", end="", flush=True)

                # 使用SDK的chat方法，这会自动处理记忆工具调用
                try:
                    response_text = client.chat(user_input)
                    print(response_text)
                    conversation_count += 1

                    # 检查是否产生了新的记忆文件
                    try:
                        current_memories = client.list_memories()
                        if current_memories:
                            print(f"[系统] Claude已存储 {len(current_memories)} 个记忆文件")
                    except:
                        pass

                except Exception as e:
                    print(f"[ERROR] 对话失败: {e}")
                    print("这可能是由于API不支持memory工具导致的")
                    print("提示：您仍可以使用 'memory_add' 命令手动添加记忆")
                    continue

            except KeyboardInterrupt:
                print("\n\n再见!")
                break
            except EOFError:
                print("\n\n再见!")
                break
            except Exception as e:
                print(f"[ERROR] 对话失败: {e}")
                print("请检查网络连接和API配置")
                continue

        print("\n会话结束！")
        print("提示：Claude已经在对话过程中自动管理了记忆内容。")
        print("使用 'memories' 命令可以查看Claude存储的信息。")

    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        print("\n请确保:")
        print("1. 设置了正确的 ANTHROPIC_API_KEY 环境变量")
        print("2. 网络连接正常")
        print("3. API 端点可访问")


if __name__ == "__main__":
    main()