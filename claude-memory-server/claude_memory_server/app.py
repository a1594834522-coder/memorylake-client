"""
Claude Memory Server FastAPI应用
"""

import time
import os
import re
import json
import zipfile
import io
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import anthropic
from anthropic.types import (
    MessageParam,
    TextBlockParam,
    ToolParam,
    ToolUseBlockParam,
    ToolResultBlockParam,
)

from .config import ServerConfig
from .memory_manager import MemoryManager
from .session_manager import SessionManager


# Pydantic模型
class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class QuestionResponse(BaseModel):
    answer: str
    session_id: str
    memory_files: List[str]


class MemoryViewRequest(BaseModel):
    path: str = "/memories"


class MemoryViewResponse(BaseModel):
    contents: str


class MemoryCreateRequest(BaseModel):
    path: str
    content: str


class MemoryResponse(BaseModel):
    message: str


class MemorySearchRequest(BaseModel):
    query: str
    file_pattern: Optional[str] = "*"


class MemorySearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_matches: int


class MemoryBackupRequest(BaseModel):
    format: str = "json"  # "json" or "zip"


class MemoryBackupResponse(BaseModel):
    backup_data: Optional[str] = None  # for JSON format
    download_url: Optional[str] = None  # for ZIP format
    message: str


class MemoryOrganizeRequest(BaseModel):
    rules: Dict[str, str]  # pattern: target_directory
    dry_run: bool = True


class MemoryOrganizeResponse(BaseModel):
    moved_files: List[str]
    message: str


def create_app(config: Optional[ServerConfig] = None) -> FastAPI:
    """
    创建FastAPI应用

    Args:
        config: 服务器配置

    Returns:
        FastAPI应用实例
    """
    if config is None:
        config = ServerConfig()

    app = FastAPI(
        title="Claude Memory Q&A API",
        version="1.0.0",
        description="Claude Memory Q&A API with intelligent memory capabilities"
    )

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局实例
    memory_manager = MemoryManager(config.memory_dir)
    session_manager = SessionManager()

    # 初始化Anthropic客户端
    try:
        client = anthropic.Anthropic(
            api_key=config.anthropic_api_key,
            base_url=config.anthropic_base_url
        )
        print("Anthropic client initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize Anthropic client: {e}")
        print("Please ensure you have the correct version of anthropic package installed")
        client = None

    def get_session(session_id: Optional[str]) -> str:
        """获取或创建会话ID"""
        return session_manager.get_session(session_id)

    def get_memory_files() -> List[str]:
        """获取记忆文件列表"""
        try:
            return memory_manager.get_memory_files()
        except Exception:
            return []

    def execute_memory_command(tool_input: Dict) -> str:
        """执行记忆工具命令"""
        command = tool_input.get("command")

        try:
            if command == "view":
                path = tool_input.get("path", "/memories")
                if path == "/memories":
                    return memory_manager.view_directory()
                else:
                    return memory_manager.view_file(path, tool_input.get("view_range"))

            elif command == "create":
                return memory_manager.create_file(
                    tool_input.get("path", ""),
                    tool_input.get("file_text", "")
                )

            elif command == "str_replace":
                return memory_manager.str_replace(
                    tool_input.get("path", ""),
                    tool_input.get("old_str", ""),
                    tool_input.get("new_str", "")
                )

            elif command == "insert":
                return memory_manager.insert_text(
                    tool_input.get("path", ""),
                    tool_input.get("insert_line", 0),
                    tool_input.get("insert_text", "")
                )

            elif command == "delete":
                return memory_manager.delete_path(tool_input.get("path", ""))

            elif command == "rename":
                return memory_manager.rename_path(
                    tool_input.get("old_path", ""),
                    tool_input.get("new_path", "")
                )

            else:
                return f"Unknown command: {command}"

        except Exception as e:
            return f"Error executing command {command}: {str(e)}"

    # API路由
    @app.get("/")
    async def root():
        return {
            "message": "Claude Memory Q&A API",
            "version": "1.0.0",
            "status": "active"
        }

    @app.post("/ask", response_model=QuestionResponse)
    async def ask_question(request: QuestionRequest):
        """问答接口"""
        try:
            session_id = get_session(request.session_id)
            messages = session_manager.get_session_messages(session_id)

            # 添加用户消息
            user_message = {"role": "user", "content": request.question}
            session_manager.add_message_to_session(session_id, user_message)

            # 定义记忆工具
            memory_tool: ToolParam = {
                "type": "memory_20250818",
                "name": "memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The memory command to execute (view, create, str_replace, insert, delete, rename)"
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory path"
                        },
                        "file_text": {
                            "type": "string",
                            "description": "Text content for file creation"
                        },
                        "old_str": {
                            "type": "string",
                            "description": "Text to replace"
                        },
                        "new_str": {
                            "type": "string",
                            "description": "New text to replace with"
                        },
                        "insert_line": {
                            "type": "integer",
                            "description": "Line number to insert text at"
                        },
                        "insert_text": {
                            "type": "string",
                            "description": "Text to insert"
                        },
                        "old_path": {
                            "type": "string",
                            "description": "Original path for rename"
                        },
                        "new_path": {
                            "type": "string",
                            "description": "New path for rename"
                        },
                        "view_range": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Line range to view [start, end]"
                        }
                    },
                    "required": ["command"]
                }
            }

            # 检查客户端是否可用
            if client is None:
                raise HTTPException(
                    status_code=503,
                    detail="Anthropic client not initialized. Please check your API configuration."
                )

            # 调用Claude API
            try:
                response = client.beta.messages.create(
                    model=config.anthropic_model,
                    max_tokens=config.max_tokens,
                    system=config.memory_system_prompt,
                    messages=messages,
                    tools=[memory_tool],
                    betas=["context-management-2025-06-27"]
                )
            except Exception as api_error:
                print(f"API Error: {api_error}")
                # 返回回退响应
                return QuestionResponse(
                    answer="I'm having trouble connecting to my AI services right now, but I've noted your message. The memory system is still working to store our conversation.",
                    session_id=session_id,
                    memory_files=get_memory_files()
                )

            # 处理响应
            assistant_content = []
            final_answer = ""

            for content in response.content:
                if content.type == "text":
                    final_answer += content.text
                    assistant_content.append({"type": "text", "text": content.text})

                elif content.type == "tool_use" and content.name == "memory":
                    tool_result = execute_memory_command(content.input)
                    assistant_content.append({
                        "type": "tool_use",
                        "id": content.id,
                        "name": content.name,
                        "input": content.input,
                    })

                    # 添加工具结果到消息并继续对话
                    messages.append({"role": "assistant", "content": assistant_content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result
                        }]
                    })

                    # 获取工具使用后的最终响应
                    try:
                        final_response = client.beta.messages.create(
                            model=config.anthropic_model,
                            max_tokens=config.max_tokens,
                            system=config.memory_system_prompt,
                            messages=messages,
                            betas=["context-management-2025-06-27"]
                        )
                    except Exception as api_error:
                        print(f"Second API Error: {api_error}")
                        final_answer = f"I executed the memory command, but I'm having trouble generating a response. Here's what I found: {tool_result}"
                        break

                    final_answer = ""
                    for final_content in final_response.content:
                        if final_content.type == "text":
                            final_answer += final_content.text

                    assistant_content = [{"type": "text", "text": final_answer}]
                    break

            # 如果没有生成最终答案，提供默认响应
            if not final_answer:
                final_answer = "I've processed your request and checked my memory. How else can I help you?"

            # 过滤空的文本内容
            filtered_assistant_content = [
                content for content in assistant_content
                if not (content.get("type") == "text" and not content.get("text", "").strip())
            ]

            # 添加助手消息到会话
            if filtered_assistant_content:
                assistant_message = {"role": "assistant", "content": filtered_assistant_content}
                session_manager.add_message_to_session(session_id, assistant_message)

            # 获取更新的记忆文件列表
            memory_files = get_memory_files()

            return QuestionResponse(
                answer=final_answer,
                session_id=session_id,
                memory_files=memory_files
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/sessions/{session_id}")
    async def get_session_info(session_id: str):
        """获取会话信息"""
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_info.session_id,
            "message_count": session_info.message_count,
            "created_at": session_info.created_at.isoformat(),
            "last_activity": session_info.last_activity.isoformat(),
            "memory_files": get_memory_files()
        }

    @app.delete("/sessions/{session_id}")
    async def clear_session(session_id: str):
        """清除会话历史"""
        success = session_manager.clear_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session cleared"}

    @app.delete("/sessions/{session_id}/delete")
    async def delete_session(session_id: str):
        """完全删除会话"""
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session deleted"}

    @app.get("/sessions")
    async def list_sessions():
        """列出所有活跃会话"""
        session_ids = session_manager.list_sessions()
        sessions_info = []

        for session_id in session_ids:
            session_info = session_manager.get_session_info(session_id)
            if session_info:
                sessions_info.append({
                    "session_id": session_info.session_id,
                    "message_count": session_info.message_count,
                    "created_at": session_info.created_at.isoformat(),
                    "last_activity": session_info.last_activity.isoformat()
                })

        return {"sessions": sessions_info, "total": len(sessions_info)}

    @app.post("/memory/view", response_model=MemoryViewResponse)
    async def view_memory(request: MemoryViewRequest):
        """查看记忆目录或文件内容"""
        try:
            if request.path == "/memories":
                result = memory_manager.view_directory()
            else:
                result = memory_manager.view_file(request.path)
            return MemoryViewResponse(contents=result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/memory/create", response_model=MemoryResponse)
    async def create_memory(request: MemoryCreateRequest):
        """创建记忆文件"""
        try:
            result = memory_manager.create_file(request.path, request.content)
            return MemoryResponse(message=result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.delete("/memory/{path:path}")
    async def delete_memory(path: str):
        """删除记忆文件或目录"""
        try:
            full_path = f"/memories/{path}"
            result = memory_manager.delete_path(full_path)
            return MemoryResponse(message=result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/memory/files")
    async def list_memory_files():
        """列出所有记忆文件"""
        return {"files": get_memory_files()}

    @app.get("/stats")
    async def get_stats():
        """获取记忆统计信息"""
        session_stats = session_manager.get_stats()
        return {
            "session_stats": session_stats,
            "memory_stats": memory_manager.get_memory_stats(),
            "config": {
                "model": config.anthropic_model,
                "max_tokens": config.max_tokens,
                "memory_dir": config.memory_dir
            }
        }

    # ==================== 高级记忆功能 API ====================

    @app.post("/memory/search", response_model=MemorySearchResponse)
    async def search_memory(request: MemorySearchRequest):
        """搜索记忆内容"""
        try:
            results = []
            total_matches = 0

            # 获取所有记忆文件
            memory_files = get_memory_files()

            # 过滤文件模式
            pattern = re.compile(request.file_pattern.replace('*', '.*'))
            filtered_files = [f for f in memory_files if pattern.match(f)]

            for file_name in filtered_files:
                try:
                    file_path = f"/memories/{file_name}"
                    content = memory_manager.view_file(file_path)

                    # 搜索匹配
                    matches = []
                    lines = content.split('\n')

                    for line_num, line in enumerate(lines, 1):
                        if re.search(re.escape(request.query), line, re.IGNORECASE):
                            matches.append({
                                "line_number": line_num,
                                "content": line.strip(),
                                "match_start": line.lower().find(request.query.lower())
                            })

                    if matches:
                        results.append({
                            "file": file_name,
                            "path": file_path,
                            "matches": matches,
                            "match_count": len(matches)
                        })
                        total_matches += len(matches)

                except Exception as e:
                    # 记录错误但继续处理其他文件
                    continue

            return MemorySearchResponse(
                results=results,
                total_matches=total_matches
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/memory/backup", response_model=MemoryBackupResponse)
    async def backup_memory(request: MemoryBackupRequest):
        """备份记忆内容"""
        try:
            memory_files = get_memory_files()

            if request.format.lower() == "json":
                # JSON格式备份
                backup_data = {
                    "backup_info": {
                        "created_at": time.time(),
                        "total_files": len(memory_files),
                        "format": "json"
                    },
                    "files": {}
                }

                for file_name in memory_files:
                    try:
                        file_path = f"/memories/{file_name}"
                        content = memory_manager.view_file(file_path)
                        backup_data["files"][file_name] = {
                            "path": file_path,
                            "content": content,
                            "size": len(content)
                        }
                    except Exception as e:
                        backup_data["files"][file_name] = {
                            "path": file_path,
                            "error": str(e)
                        }

                return MemoryBackupResponse(
                    backup_data=json.dumps(backup_data, indent=2, ensure_ascii=False),
                    message=f"成功备份 {len(memory_files)} 个记忆文件"
                )

            elif request.format.lower() == "zip":
                # ZIP格式备份
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_name in memory_files:
                        try:
                            file_path = f"/memories/{file_name}"
                            content = memory_manager.view_file(file_path)
                            zip_file.writestr(file_name, content)
                        except Exception:
                            continue

                zip_buffer.seek(0)
                # 在实际应用中，这里应该保存到文件系统或云存储
                backup_filename = f"memory_backup_{int(time.time())}.zip"

                return MemoryBackupResponse(
                    download_url=f"/downloads/{backup_filename}",
                    message=f"成功创建ZIP备份: {backup_filename}"
                )

            else:
                raise HTTPException(status_code=400, detail="不支持的备份格式")

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/memory/organize", response_model=MemoryOrganizeResponse)
    async def organize_memory(request: MemoryOrganizeRequest):
        """整理记忆文件"""
        try:
            moved_files = []
            memory_files = get_memory_files()

            for pattern, target_dir in request.rules.items():
                try:
                    # 编译正则表达式
                    regex = re.compile(pattern)

                    # 确保目标目录路径正确
                    if not target_dir.startswith('/memories'):
                        target_dir = f"/memories/{target_dir.lstrip('/')}"
                    if not target_dir.endswith('/'):
                        target_dir += '/'

                    # 查找匹配的文件
                    matching_files = [f for f in memory_files if regex.match(f)]

                    for file_name in matching_files:
                        old_path = f"/memories/{file_name}"
                        new_path = f"{target_dir}{file_name}"

                        if not request.dry_run:
                            try:
                                # 创建目标目录（如果不存在）
                                memory_manager.create_file(f"{target_dir}.keep", "")
                                # 重命名文件
                                result = memory_manager.rename_path(old_path, new_path)
                                if "成功" in result or "renamed" in result.lower():
                                    moved_files.append(f"{old_path} -> {new_path}")
                            except Exception as e:
                                continue
                        else:
                            moved_files.append(f"{old_path} -> {new_path} (预览)")

                except Exception as e:
                    continue

            mode = "实际整理" if not request.dry_run else "预览模式"
            message = f"{mode}完成，处理了 {len(moved_files)} 个文件"

            return MemoryOrganizeResponse(
                moved_files=moved_files,
                message=message
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app