from __future__ import annotations

import sys
import types
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

import pytest
from pydantic import BaseModel, ConfigDict

if "anthropic" not in sys.modules:
    anthropic_module = types.ModuleType("anthropic")
    sys.modules["anthropic"] = anthropic_module

    class _DummyMessages:
        def create(self, **_: Any) -> types.SimpleNamespace:
            return types.SimpleNamespace(content=[])

    class _DummyBeta:
        def __init__(self) -> None:
            self.messages: _DummyMessages = _DummyMessages()

    class Anthropic:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.beta: _DummyBeta = _DummyBeta()

    anthropic_module_any: Any = anthropic_module
    anthropic_module_any.Anthropic = Anthropic

    anthropic_lib_module = types.ModuleType("anthropic.lib")
    anthropic_module_any.lib = anthropic_lib_module
    sys.modules["anthropic.lib"] = anthropic_lib_module

    anthropic_lib_tools_module = types.ModuleType("anthropic.lib.tools")
    anthropic_lib_module_any: Any = anthropic_lib_module
    anthropic_lib_module_any.tools = anthropic_lib_tools_module
    sys.modules["anthropic.lib.tools"] = anthropic_lib_tools_module

    anthropic_types_module = types.ModuleType("anthropic.types")
    anthropic_module_any.types = anthropic_types_module
    sys.modules["anthropic.types"] = anthropic_types_module

    anthropic_types_beta_module = types.ModuleType("anthropic.types.beta")
    anthropic_types_module_any: Any = anthropic_types_module
    anthropic_types_module_any.beta = anthropic_types_beta_module
    sys.modules["anthropic.types.beta"] = anthropic_types_beta_module

    class BetaAbstractMemoryTool:
        def __init__(self) -> None:
            pass

        def execute(self, command: "BetaMemoryTool20250818Command") -> Any:
            handler = getattr(self, command.command)
            return handler(command)

    setattr(anthropic_lib_tools_module, "BetaAbstractMemoryTool", BetaAbstractMemoryTool)

    class BetaMemoryTool20250818Command(BaseModel):
        command: str
        path: str | None = None
        file_text: str | None = None
        insert_line: int | None = None
        insert_text: str | None = None
        old_str: str | None = None
        new_str: str | None = None
        old_path: str | None = None
        new_path: str | None = None
        view_range: list[int] | None = None

        model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    class BetaMemoryTool20250818ViewCommand(BetaMemoryTool20250818Command):
        command: str = "view"
        path: str | None = None

    class BetaMemoryTool20250818CreateCommand(BetaMemoryTool20250818Command):
        command: str = "create"
        path: str | None = None
        file_text: str | None = None

    class BetaMemoryTool20250818StrReplaceCommand(BetaMemoryTool20250818Command):
        command: str = "str_replace"
        path: str | None = None
        old_str: str | None = None
        new_str: str | None = None

    class BetaMemoryTool20250818InsertCommand(BetaMemoryTool20250818Command):
        command: str = "insert"
        path: str | None = None
        insert_line: int | None = None
        insert_text: str | None = None

    class BetaMemoryTool20250818DeleteCommand(BetaMemoryTool20250818Command):
        command: str = "delete"
        path: str | None = None

    class BetaMemoryTool20250818RenameCommand(BetaMemoryTool20250818Command):
        command: str = "rename"
        old_path: str | None = None
        new_path: str | None = None

    anthropic_types_beta_any: Any = anthropic_types_beta_module
    anthropic_types_beta_any.BetaContentBlockParam = dict
    anthropic_types_beta_any.BetaMessageParam = dict
    anthropic_types_beta_any.BetaMemoryTool20250818Command = BetaMemoryTool20250818Command
    anthropic_types_beta_any.BetaMemoryTool20250818CreateCommand = BetaMemoryTool20250818CreateCommand
    anthropic_types_beta_any.BetaMemoryTool20250818DeleteCommand = BetaMemoryTool20250818DeleteCommand
    anthropic_types_beta_any.BetaMemoryTool20250818InsertCommand = BetaMemoryTool20250818InsertCommand
    anthropic_types_beta_any.BetaMemoryTool20250818RenameCommand = BetaMemoryTool20250818RenameCommand
    anthropic_types_beta_any.BetaMemoryTool20250818StrReplaceCommand = BetaMemoryTool20250818StrReplaceCommand
    anthropic_types_beta_any.BetaMemoryTool20250818ViewCommand = BetaMemoryTool20250818ViewCommand


from example import chat as chat_example
from memorylake.memorytool import (
    MemoryTool,
    MemoryToolOperationError,
    MemoryToolPathError,
)

handle_local_command = getattr(chat_example, "_handle_local_command")
run_exec_command = getattr(chat_example, "_run_exec_command")


def test_memorytool_file_lifecycle_and_stats(tmp_path: Any) -> None:
    tool = MemoryTool(base_path=tmp_path)

    tool.create_file("/memories/note.txt", "first")
    tool.insert_line("/memories/note.txt", 1, "second")
    tool.replace_text("/memories/note.txt", "first", "updated")

    view_output = tool.view_path("/memories/note.txt", view_range=(1, 3))
    assert "File: /memories/note.txt" in view_output
    assert "updated" in view_output
    assert "second" in view_output

    tool.rename_path("/memories/note.txt", "/memories/archive/note.txt")
    assert tool.memory_exists("/memories/archive/note.txt")

    entries = tool.list_memories("/memories")
    assert "/memories/archive/" in entries
    assert "/memories/archive/note.txt" in entries

    stats = tool.stats()
    assert stats["files"] == 1
    assert stats["directories"] >= 1
    assert stats["bytes"] > 0

    tool.delete_path("/memories/archive/note.txt")
    stats_after_delete = tool.stats()
    assert stats_after_delete["files"] == 0

    tool.clear_all()
    assert tool.stats() == {"files": 0, "directories": 0, "bytes": 0}


def test_memorytool_execute_payload_and_errors(tmp_path: Any) -> None:
    tool = MemoryTool(base_path=tmp_path)

    result = tool.execute_tool_payload(
        {"command": "create", "path": "/memories/commands.txt", "file_text": "payload"}
    )
    assert "File created" in result

    view_result = tool.execute_tool_payload({"command": "view", "path": "/memories/commands.txt"})
    assert "payload" in view_result

    with pytest.raises(MemoryToolOperationError):
        tool.replace_text("/memories/commands.txt", "missing", "value")

    with pytest.raises(MemoryToolPathError):
        tool.create_file("memories/bad.txt", "oops")


def test_example_local_commands_and_exec(tmp_path: Any, capsys: pytest.CaptureFixture[str]) -> None:
    tool = MemoryTool(base_path=tmp_path)
    menu = {
        "help": "help",
        "memory-create": "",
        "memory-list": "",
        "memory-view": "",
    }

    assert handle_local_command("/memory-create /memories/demo.txt hello", tool, menu)
    output = capsys.readouterr().out
    assert "已创建" in output

    assert handle_local_command("/memory-list", tool, menu)
    output = capsys.readouterr().out
    assert "/memories/demo.txt" in output

    assert handle_local_command("/memory-view /memories/demo.txt 1 -1", tool, menu)
    output = capsys.readouterr().out
    assert "File: /memories/demo.txt" in output

    run_exec_command(tool, ["rename", "/memories/demo.txt", "/memories/demo2.txt"])
    output = capsys.readouterr().out
    assert "Renamed" in output

    run_exec_command(tool, ["delete", "/memories/demo2.txt"])
    output = capsys.readouterr().out
    assert "File deleted" in output


def test_memorylake_init_missing_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    import importlib
    import sys

    saved_module_names = [
        "anthropic",
        "anthropic.lib",
        "anthropic.lib.tools",
        "anthropic.types",
        "anthropic.types.beta",
    ]

    saved_modules = {name: sys.modules.pop(name, None) for name in saved_module_names}
    original_memorylake = sys.modules.pop("memorylake", None)
    original_memorytool = sys.modules.pop("memorylake.memorytool", None)

    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, Any] | None = None,
        locals: Mapping[str, Any] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> Any:
        if name.startswith("anthropic"):
            raise ModuleNotFoundError(f"No module named '{name}'", name=name)
        fromlist_tuple: tuple[str, ...] = tuple(fromlist) if fromlist is not None else ()
        return real_import(name, globals, locals, fromlist_tuple, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    try:
        module = importlib.import_module("memorylake")
        with pytest.raises(ModuleNotFoundError):
            module.__getattr__("MemoryTool")
        assert "__version__" in module.__dir__()
    finally:
        sys.modules.pop("memorylake", None)
        sys.modules.pop("memorylake.memorytool", None)

        if original_memorytool is not None:
            sys.modules["memorylake.memorytool"] = original_memorytool
        if original_memorylake is not None:
            sys.modules["memorylake"] = original_memorylake

        for name in saved_module_names:
            module_obj = saved_modules[name]
            if module_obj is not None:
                sys.modules[name] = module_obj
