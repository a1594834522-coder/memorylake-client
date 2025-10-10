"""
Claude Memory SDK 安装配置
"""

from setuptools import setup, find_packages
import os

# 读取README文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements文件
def read_requirements():
    """读取requirements文件"""
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return [
        "requests>=2.25.0",
        "pydantic>=2.0.0"
    ]

setup(
    name="claude-memory-sdk",
    version="1.0.0",
    author="Claude Memory SDK Team",
    author_email="support@example.com",
    description="Python SDK for Claude Memory Q&A API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/claude-memory-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
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
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
        "docs": [
            "mkdocs>=1.2",
            "mkdocs-material>=7.0",
        ],
    },
    keywords="claude ai memory api sdk anthropic",
    project_urls={
        "Bug Reports": "https://github.com/example/claude-memory-sdk/issues",
        "Source": "https://github.com/example/claude-memory-sdk",
        "Documentation": "https://claude-memory-sdk.readthedocs.io/",
    },
    include_package_data=True,
    zip_safe=False,
)