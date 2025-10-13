"""
Public interface for the lightweight memorylake package.

Only the ``MemoryTool`` class and its related exceptions are exported.
"""

__all__ = [
    "MemoryTool",
    "MemoryToolError",
    "MemoryToolOperationError",
    "MemoryToolPathError",
    "__version__",
]

__version__ = "0.1.0"

from .memorytool import (  # noqa: E402  (import after __all__/__version__)
    MemoryTool,
    MemoryToolError,
    MemoryToolOperationError,
    MemoryToolPathError,
)
