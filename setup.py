#!/usr/bin/env python3
"""
Memory Lake SDK 安装配置
"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Memory Lake SDK - 简化开发者对 Claude Memory Tool 使用的 Python SDK"

# 读取版本信息
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'memory_lake_sdk', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return "0.1.0"

setup(
    name="memory-lake-sdk",
    version=get_version(),
    author="Memory Lake Team",
    author_email="team@memorylake.ai",
    description="简化开发者对 Claude Memory Tool 使用的 Python SDK",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/memorylake/memory-lake-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/memorylake/memory-lake-sdk/issues",
        "Documentation": "https://github.com/memorylake/memory-lake-sdk/docs",
        "Source Code": "https://github.com/memorylake/memory-lake-sdk",
        "Changelog": "https://github.com/memorylake/memory-lake-sdk/blob/main/CHANGELOG.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=[
        "anthropic>=0.39.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "claude-memory-chat=memory_lake_sdk.examples.basic_chat:main",
            "claude-memory-manage=memory_lake_sdk.examples.manage_memory:main",
            "memory-lake-chat=memory_lake_sdk.examples.basic_chat:main",
            "memory-lake-manage=memory_lake_sdk.examples.manage_memory:main",
        ],
    },
    include_package_data=True,
    package_data={
        "memory_lake_sdk": [
            "examples/*.py",
            "examples/*.md",
        ],
    },
    keywords=[
        "claude",
        "anthropic",
        "ai",
        "memory",
        "sdk",
        "chatbot",
        "conversation",
        "context",
        "python",
    ],
    license="MIT",
    license_files=["LICENSE"],
    zip_safe=False,
)
