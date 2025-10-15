"""Public interface for the MemoryLake client package."""

__version__: str = "0.1.0"

__all__ = ["MemoryTool", "MemoryToolError", "MemoryToolOperationError", "MemoryToolPathError", "__version__"]

try:
    from .memorytool import (
        MemoryTool,
        MemoryToolError,
        MemoryToolOperationError,
        MemoryToolPathError,
    )
except ModuleNotFoundError as exc:
    if exc.name and exc.name.startswith("anthropic"):
        _IMPORT_ERROR = exc

        def __getattr__(name: str):
            if name in {"MemoryTool", "MemoryToolError", "MemoryToolOperationError", "MemoryToolPathError"}:
                raise ModuleNotFoundError(
                    "memorylake.memorytool requires the 'anthropic' package. Install the project dependencies to use MemoryTool."
                ) from _IMPORT_ERROR
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

        def __dir__():
            return sorted(__all__)
    else:
        raise
