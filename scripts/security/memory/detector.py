"""
Auto-detection of the memory backend configured in Hermes.

Priority:
    1. Environment variable ANDORINA_MEMORY_BACKEND
    2. Auto-detection: Hindsight → Hermes API → Noop
"""

import os
from typing import Optional

from .backend import MemoryBackend, NoopBackend
from .hindsight import HindsightBackend
from .hermes_memory import HermesMemoryBackend


def detect_memory_backend() -> MemoryBackend:
    """Auto-detect the available memory backend.

    Returns:
        MemoryBackend instance (never None — falls back to NoopBackend)
    """
    # 1. Environment variable (explicit configuration)
    backend_env = os.environ.get("ANDORINA_MEMORY_BACKEND", "").lower()
    if backend_env == "hindsight":
        backend = HindsightBackend()
        if backend.is_available():
            return backend
    elif backend_env == "hermes":
        backend = HermesMemoryBackend()
        if backend.is_available():
            return backend
    elif backend_env == "none":
        return NoopBackend()

    # 2. Auto-detection: probar Hindsight primero (compatibilidad)
    hindsight = HindsightBackend()
    if hindsight.is_available():
        return hindsight

    # 3. Try Hermes native API
    hermes = HermesMemoryBackend()
    if hermes.is_available():
        return hermes

    # 4. Safe fallback: no memory
    return NoopBackend()


# Singleton to avoid multiple detections
_memory_backend: Optional[MemoryBackend] = None


def get_memory_backend() -> MemoryBackend:
    """Get the memory backend (singleton).

    Returns:
        MemoryBackend instance
    """
    global _memory_backend
    if _memory_backend is None:
        _memory_backend = detect_memory_backend()
    return _memory_backend


def reset_memory_backend() -> None:
    """Reset singleton to force re-detection."""
    global _memory_backend
    _memory_backend = None
