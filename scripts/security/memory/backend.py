"""
Interfaz abstracta para backends de memoria de Andorina.

Permite soportar Hindsight, Mnemosyne, Honcho, o cualquier otro backend
compatible con Hermes Agent, sin hardcodear dependencias específicas.

Arquitectura:
    MemoryBackend (ABC)
    ├── HindsightBackend    — PostgreSQL embebido (legacy)
    ├── HermesMemoryBackend — API nativa de Hermes (recomendado)
    └── NoopBackend         — Sin memoria (fallback seguro)

Uso:
    from security.memory import MemoryBackend, get_memory_backend
    backend = get_memory_backend()
    if backend.is_available():
        backend.purge("34600000000@s.whatsapp.net")
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class MemoryBackend(ABC):
    """Interfaz abstracta para backends de memoria."""

    @abstractmethod
    def purge(self, jid: str) -> bool:
        """Purga toda la memoria asociada a un JID.

        Args:
            jid: JID del usuario (ej: "34600000000@s.whatsapp.net")

        Returns:
            True si la purga fue exitosa, False en caso contrario
        """
        pass

    @abstractmethod
    def search(self, jid: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca en la memoria de un JID.

        Args:
            jid: JID del usuario
            query: Texto a buscar
            limit: Número máximo de resultados

        Returns:
            Lista de resultados con formato {"content": str, "score": float, ...}
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el backend está disponible y funcionando.

        Returns:
            True si está disponible, False en caso contrario
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del backend.

        Returns:
            Dict con información del estado:
            {"backend": str, "available": bool, ...}
        """
        pass

    def get_name(self) -> str:
        """Nombre legible del backend."""
        return self.__class__.__name__


class NoopBackend(MemoryBackend):
    """Backend que no hace nada — fallback seguro cuando no hay memoria disponible."""

    def purge(self, jid: str) -> bool:
        return True

    def search(self, jid: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return []

    def is_available(self) -> bool:
        return False

    def get_status(self) -> Dict[str, Any]:
        return {"backend": "noop", "available": False, "reason": "no memory backend configured"}
