"""
memory/ — Abstract memory backends for Andorina V2.0.

Supports Hindsight, Mnemosyne, Honcho, or any memory backend
compatible with Hermes Agent.
"""

from .backend import MemoryBackend
from .detector import detect_memory_backend, get_memory_backend

__all__ = ["MemoryBackend", "detect_memory_backend", "get_memory_backend"]
