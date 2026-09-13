"""
Implementación genérica de MemoryBackend para cualquier backend de Hermes.

Usa la API nativa de Hermes Agent para purgar/buscar memoria,
sin depender de un backend específico.
"""

import subprocess
import json
import shutil
from typing import List, Dict, Any, Optional

from .backend import MemoryBackend


class HermesMemoryBackend(MemoryBackend):
    """Implementación genérica para backends de memoria de Hermes.

    Usa `hermes memory purge` y `hermes memory search` para interactuar
    con el backend configurado (Mnemosyne, Honcho, Hindsight, etc).
    """

    def __init__(self):
        self._hermes_cmd: Optional[str] = self._detect_hermes()

    def _detect_hermes(self) -> Optional[str]:
        """Detecta el comando de Hermes en el PATH."""
        return shutil.which("hermes")

    def _run_hermes(self, *args: str, timeout: int = 15) -> tuple[bool, str]:
        """Ejecuta un comando de Hermes y retorna (éxito, output)."""
        if not self._hermes_cmd:
            return False, "hermes command not found"
        try:
            cmd = [self._hermes_cmd] + list(args)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.returncode == 0, r.stdout.strip() or r.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "timeout"
        except Exception as e:
            return False, str(e)

    def purge(self, jid: str) -> bool:
        """Purga memoria usando la API de Hermes."""
        ok, _ = self._run_hermes("memory", "purge", jid, timeout=15)
        return ok

    def search(self, jid: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca usando la API de Hermes."""
        ok, output = self._run_hermes(
            "memory", "search", jid, query, "--limit", str(limit), timeout=15
        )
        if not ok:
            return []
        try:
            data = json.loads(output)
            if isinstance(data, list):
                return data[:limit]
            if isinstance(data, dict):
                return data.get("results", [])[:limit]
        except json.JSONDecodeError:
            pass
        return []

    def is_available(self) -> bool:
        """Verifica si Hermes está disponible."""
        if not self._hermes_cmd:
            return False
        ok, _ = self._run_hermes("--version", timeout=5)
        return ok

    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado del backend."""
        available = self.is_available()
        status: Dict[str, Any] = {
            "backend": "hermes_provider",
            "available": available,
            "hermes_cmd": self._hermes_cmd,
        }
        if available:
            ok, output = self._run_hermes("memory", "status", timeout=5)
            if ok:
                try:
                    status["provider"] = json.loads(output)
                except json.JSONDecodeError:
                    status["provider"] = output
        return status
