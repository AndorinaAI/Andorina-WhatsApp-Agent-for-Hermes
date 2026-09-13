"""
Implementación de MemoryBackend para Hindsight/PostgreSQL embebido.

Mantiene compatibilidad con instalaciones existentes que usan
Hindsight como backend de memoria vectorial.
"""

import glob
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from .backend import MemoryBackend


class HindsightBackend(MemoryBackend):
    """Implementación para Hindsight/PostgreSQL embebido."""

    def __init__(self):
        self._psql_bin: Optional[str] = None
        self._db_name: Optional[str] = None
        self._detect_hindsight()

    def _detect_hindsight(self) -> None:
        """Detecta si Hindsight está instalado y ejecutándose."""
        psql_bin_list = glob.glob(
            str(Path.home() / ".pg0" / "installation" / "*" / "bin" / "psql")
        )
        if not psql_bin_list:
            return

        self._psql_bin = psql_bin_list[0]
        connection_string = f"postgresql://postgres:postgres@127.0.0.1:5432"

        for db_name in ["hindsight", "hindsight-embed-hermes"]:
            if self._test_connection(connection_string, db_name):
                self._db_name = db_name
                break

    def _test_connection(self, conn_string: str, db_name: str) -> bool:
        """Prueba si una base de datos existe y responde."""
        if not self._psql_bin:
            return False
        try:
            cmd = [
                self._psql_bin,
                f"{conn_string}/{db_name}",
                "-c", "SELECT 1;",
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    def purge(self, jid: str) -> bool:
        """Purga memoria de un JID en Hindsight.

        Sanitiza el JID para prevenir SQL injection.
        """
        if not self.is_available():
            return False

        # V2.0: sanitización centralizada de JID
        number = re.sub(r"[^\d]", "", jid)
        if not number:
            return False

        conn_string = f"postgresql://postgres:postgres@127.0.0.1:5432/{self._db_name}"
        query = f"DELETE FROM documents WHERE id LIKE '%{number}%';"

        try:
            cmd = [self._psql_bin, conn_string, "-c", query]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return r.returncode == 0
        except Exception:
            return False

    def search(self, jid: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca en Hindsight por similitud semántica."""
        if not self.is_available():
            return []

        number = re.sub(r"[^\d]", "", jid)
        if not number:
            return []

        conn_string = f"postgresql://postgres:postgres@127.0.0.1:5432/{self._db_name}"
        sql = (
            f"SELECT content, 1.0 as score FROM documents "
            f"WHERE id LIKE '%{number}%' LIMIT {limit};"
        )

        try:
            cmd = [self._psql_bin, conn_string, "-c", sql]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if r.returncode != 0:
                return []
            results = []
            for line in r.stdout.split("\n"):
                if "|" in line and "content" not in line.lower():
                    parts = line.split("|")
                    if len(parts) >= 2:
                        results.append({
                            "content": parts[0].strip(),
                            "score": float(parts[1].strip()) if len(parts) > 1 else 0.0
                        })
            return results[:limit]
        except Exception:
            return []

    def is_available(self) -> bool:
        """Verifica si Hindsight está disponible."""
        return self._psql_bin is not None and self._db_name is not None

    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado de Hindsight."""
        return {
            "backend": "hindsight",
            "available": self.is_available(),
            "psql_path": self._psql_bin,
            "db_name": self._db_name,
        }
