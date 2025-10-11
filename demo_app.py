#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Memory SDK 演示应用程序

用于测试SDK功能的简单交互式应用
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_memory_sdk import ClaudeMemoryClient


def main():
    """主应用程序"""
    print("Claude Memory SDK 演示应用")
    print("=" * 50)

    # 设置环境变量
    os.environ.setdefault('ANTHROPIC_API_KEY', 'de4751f251a8486bb38dde538c20f3c6.Fmd1Nm0X5wvjVVhe')
    os.environ.setdefault('ANTHROPIC_BASE_URL', 'https://open.bigmodel.cn/api/anthropic')
    os.environ.setdefault('ANTHROPIC_MODEL', 'GLM-4.6')

    try:
        # 初始化客户端
        print("正在初始化客户端...")
        client = ClaudeMemoryClient()
        print("[OK] 客户端初始化成功!\n")

        # 使用内置的交互式循环
        client.interactive_loop()

    except Exception as e:
        print(f"[ERROR] 应用启动失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())