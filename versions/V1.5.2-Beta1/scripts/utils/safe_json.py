import json
import pathlib
from filelock import FileLock, Timeout

def read_json_safe(path, default=None):
    """Lee un archivo JSON de forma segura usando un candado temporal."""
    path = pathlib.Path(path)
    lock_path = str(path) + ".lock"
    # Bloqueamos máximo 3 segundos, si en 3 segundos no suelta, falla.
    lock = FileLock(lock_path, timeout=3)
    
    try:
        with lock:
            if not path.exists():
                return default
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                return default
            return json.loads(content)
    except Exception as e:
        print(f"Error leyendo {path}: {e}")
        return default

def write_json_safe(path, data):
    """Escribe un archivo JSON de forma segura usando un candado temporal."""
    path = pathlib.Path(path)
    lock_path = str(path) + ".lock"
    lock = FileLock(lock_path, timeout=3)
    
    try:
        with lock:
            # Atomicidad básica: escribir en un temporal y renombrar (opcional pero más seguro)
            # Para no complicarlo en V2.0, usamos escritura directa protegida por el lock
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
    except Exception as e:
        print(f"Error escribiendo {path}: {e}")
        return False
