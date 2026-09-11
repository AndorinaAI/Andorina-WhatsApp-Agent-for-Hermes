"""
security/knowledge_retrieval.py — Motor RAG (Retrieval-Augmented Generation).

FASE 2 del refactor V1.6: extraído de orchestrator_hook.py (L15-460).
Contiene las funciones de carga de knowledge base, BM25, embeddings y resolución de JIDs.
Las llamadas en main() de orchestrator_hook.py permanecen igual — solo cambia el origen del import.
"""
import sys
import os
import json
import sqlite3
from pathlib import Path

# Import centralized JID utilities (unified in utils/jids.py)
sys.path.append(str(Path(__file__).parent.parent))
from utils.jids import normalize_text as _jids_normalize_text, resolve_lid_to_phone


# ── BM25 Knowledge Retrieval ─────────────────────────────────────────────────
_ES_STOPWORDS = {
    "a","al","ante","con","de","del","desde","el","en","entre","es","esta",
    "este","estos","estas","hay","la","las","le","les","lo","los","mas","me",
    "mi","mis","muy","no","nos","o","para","pero","por","que","se","si",
    "sin","sobre","su","sus","te","tu","tus","un","una","uno","unos","unas",
    "y","ya","yo","he","ha","han","hola","porfa","por favor","teneis","tenéis",
    "cual","cuando","como","donde","quien","cuales",
}

def _normalize(text: str) -> str:
    """Lowercase + strip accents + stem Spanish plurals for BM25.
    Uses jids.normalize_text() as base, then adds BM25-specific stemming."""
    # Base normalization from centralized jids.py
    normalized = _jids_normalize_text(text)
    # Simple suffix stemmer: strip -es, -s (plural forms) for BM25
    tokens = []
    for w in normalized.split():
        if w in _ES_STOPWORDS:
            continue
        if len(w) > 5 and w.endswith("es"):
            w = w[:-2]   # talleres → taller, programaciones → programacion
        elif len(w) > 4 and w.endswith("s"):
            w = w[:-1]   # horarios → horario, peliculas → pelicula
        tokens.append(w)
    return " ".join(tokens)


def _load_chunks(knowledge_dir: str, max_chars_per_chunk: int = 800) -> list:
    """Carga y chunkea todos los archivos del knowledge/ (incluyendo subcarpetas).
    Devuelve list of (filename, chunk_text).
    Soporta: .txt .md .csv .json .pdf .docx .doc .pptx .xlsx .xls .sqlite .odt .ods
    """
    kdir = Path(knowledge_dir)
    if not kdir.is_dir():
        return []

    # Import the rich extractor from soul_sync (supports PDF/DOCX/XLSX/SQLite etc.)
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from security.soul_sync import extract_file_text as _extract
    except Exception:
        _extract = None

    _SUPPORTED = {".txt", ".md", ".csv", ".json",
                  ".pdf", ".docx", ".doc", ".pptx",
                  ".xlsx", ".xls", ".db", ".sqlite", ".sqlite3",
                  ".odt", ".ods", ".odp"}

    chunks = []
    for f in sorted(kdir.rglob("*")):
        if not f.is_file():
            continue
        if f.name.startswith("_") and f.suffix in (".pkl", ".json"):
            continue  # skip cache files
        ext = f.suffix.lower()
        if ext not in _SUPPORTED:
            continue
        try:
            if _extract and ext not in (".txt", ".md", ".csv"):
                content = _extract(f)
            else:
                content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not content:
            continue
        # Skip error strings returned by extract_file_text (e.g. "[PDF no legible: …]")
        if content.startswith("[") and ("no legible" in content or "Error leyendo" in content):
            continue
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 > max_chars_per_chunk:
                if current_chunk:
                    chunks.append((f.name, current_chunk.strip()))
                current_chunk = para
            else:
                current_chunk = (current_chunk + "\n\n" + para).strip()
        if current_chunk:
            chunks.append((f.name, current_chunk.strip()))
    return chunks


def _bm25_retrieve(chunks: list, query: str, top_k: int = 3) -> list:
    """BM25 retrieval. Devuelve list of (filename, chunk_text) ordenados por relevancia.
    Fallback a keyword-matching si rank_bm25 no está instalado.
    """
    if not chunks or not query:
        return []

    try:
        from rank_bm25 import BM25Okapi
        tokenized_corpus = [_normalize(c[1]).split() for c in chunks]
        tokenized_query = _normalize(query).split()
        if not tokenized_query:
            return []
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(chunks[i][0], chunks[i][1]) for i, score in ranked[:top_k] if score > 0]

    except ImportError:
        # Fallback: simple TF keyword scoring — no external deps needed
        q_terms = set(_normalize(query).split())
        if not q_terms:
            return chunks[:top_k]
        scored = []
        for fname, text in chunks:
            words = _normalize(text).split()
            if not words:
                continue
            hits = sum(words.count(t) for t in q_terms)
            score = hits / len(words)  # term frequency
            scored.append((score, fname, text))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(fname, text) for score, fname, text in scored[:top_k] if score > 0] or chunks[:top_k]


def _read_hermes_model_config() -> dict:
    """Lee base_url y provider del LLM desde ~/.hermes/config.yaml."""
    try:
        hermes_dir = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
        cfg_file = hermes_dir / "config.yaml"
        if not cfg_file.exists():
            return {}
        from ruamel.yaml import YAML
        yaml = YAML()
        with open(cfg_file) as f:
            cfg = yaml.load(f)
        model_cfg = cfg.get("model", {}) or {}
        return {
            "base_url": model_cfg.get("base_url", "") or "",
            "provider":  model_cfg.get("provider", "") or "",
        }
    except Exception:
        return {}


def _get_embedding(text: str, model: str, base_url: str) -> list | None:
    """
    Obtiene el vector de embedding para un texto.
    Cadena de intentos:
      1. POST {base_url}/embeddings  (OpenAI-compatible: LM Studio, Ollama ≥0.1.24, OpenAI, vLLM…)
      2. POST {ollama_root}/api/embeddings  (Ollama legacy)
      3. sentence_transformers.SentenceTransformer(model) (local, sin servidor)
    Devuelve list[float] o None si ningún backend está disponible.
    """
    import json as _json
    import urllib.request
    import urllib.parse

    # ── 1. OpenAI-compatible endpoint ──────────────────────────────────────────
    if base_url and model:
        try:
            api_url = base_url.rstrip("/") + "/embeddings"
            payload = _json.dumps({"model": model, "input": text}).encode()
            req = urllib.request.Request(
                api_url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return _json.loads(resp.read())["data"][0]["embedding"]
        except Exception:
            pass

        # ── 2. Ollama legacy  /api/embeddings ──────────────────────────────────
        try:
            parsed = urllib.parse.urlparse(base_url)
            ollama_url = f"{parsed.scheme}://{parsed.netloc}/api/embeddings"
            payload = _json.dumps({"model": model, "prompt": text}).encode()
            req = urllib.request.Request(
                ollama_url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = _json.loads(resp.read())
                if result.get("embedding"):
                    return result["embedding"]
        except Exception:
            pass

    # ── 3. sentence-transformers (local, sin servidor) ─────────────────────────
    if model:
        try:
            from sentence_transformers import SentenceTransformer
            _st_model = SentenceTransformer(model)
            return _st_model.encode([text])[0].tolist()
        except Exception:
            pass

    return None


def _embed_retrieve(chunks: list, query: str, model: str, base_url: str,
                    cache_path: Path, top_k: int = 2, min_sim: float = 0.3) -> list:
    """
    Recuperación semántica por embeddings con caché hash-based.
    Devuelve list of (filename, chunk_text) ordenados por similitud coseno.
    Si el backend no está disponible, devuelve [].
    """
    if not chunks or not query or not model:
        return []
    try:
        import hashlib
        import pickle
        import numpy as np
    except ImportError:
        return []

    content_hash = hashlib.sha256(
        ("\n".join(f"{c[0]}:{c[1]}" for c in chunks) + model).encode()
    ).hexdigest()[:16]

    embeddings = None
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as fh:
                cached = pickle.load(fh)
            if cached.get("hash") == content_hash:
                embeddings = cached["embeddings"]
        except Exception:
            pass

    if embeddings is None:
        vecs = []
        for _, chunk_text in chunks:
            vec = _get_embedding(chunk_text, model, base_url)
            if vec is None:
                return []  # backend unavailable
            vecs.append(vec)
        embeddings = np.array(vecs, dtype=np.float32)
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as fh:
                pickle.dump({"hash": content_hash, "embeddings": embeddings}, fh)
        except Exception:
            pass

    query_vec = _get_embedding(query, model, base_url)
    if query_vec is None:
        return []

    q = np.array(query_vec, dtype=np.float32)
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q)
    sims = np.dot(embeddings, q) / np.where(norms == 0, 1e-9, norms)
    ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)
    return [(chunks[i][0], chunks[i][1]) for i, sim in ranked[:top_k] if sim > min_sim]


# Prefijos de rutas PERMITIDAS para el knowledge (fuera de estos = bloqueado)
_ALLOWED_KB_PREFIXES: tuple = (
    str(Path.home()),          # /home/<user>/...
    "/tmp/andorina_kb",        # directorio temporal específico si se usa
)
_BLOCKED_KB_PREFIXES: tuple = (
    "/etc", "/root", "/proc", "/sys", "/dev",
    "/bin", "/sbin", "/usr/bin", "/usr/sbin",
    "/boot", "/lib", "/lib64",
)


def _is_safe_knowledge_dir(path: str) -> bool:
    """Valida que la ruta de knowledge sea segura y no exponga ficheros del sistema."""
    if not path:
        return False
    resolved = str(Path(path).resolve())
    # Bloquear explícitamente rutas de sistema
    for blocked in _BLOCKED_KB_PREFIXES:
        if resolved.startswith(blocked):
            print(f"[knowledge] ⛔ Ruta bloqueada (sistema): {resolved}")
            return False
    # Solo permitir rutas dentro del home del usuario o prefijos explícitos
    for allowed in _ALLOWED_KB_PREFIXES:
        if resolved.startswith(allowed):
            return True
    print(f"[knowledge] ⛔ Ruta rechazada (fuera de zona segura): {resolved}")
    return False


def _build_knowledge_context(knowledge_dir: str, query: str, rules: dict) -> str:
    """
    Orquestador principal de Knowledge Retrieval.
    Combina BM25 (siempre disponible) + embeddings (si knowledge_embed_model configurado).
    Devuelve el bloque [KNOWLEDGE BASE...] listo para inyectar en el prompt del LLM.
    Garantías:
      - Solo lee directorios dentro del home del usuario (bloquea /etc, /root, etc.)
      - Si hay ≤ MAX_SMALL_KB chunks, se inyectan todos (colección pequeña).
      - Si BM25+embed no devuelven nada (query sin overlap), se inyectan los N chunks
        más largos como fallback para que el LLM nunca se quede sin contexto.
    """
    if not knowledge_dir or not query:
        return ""

    # ── Validación de seguridad de ruta ──────────────────────────────────────
    if not _is_safe_knowledge_dir(knowledge_dir):
        return ""

    chunks = _load_chunks(knowledge_dir)
    if not chunks:
        return ""

    MAX_SMALL_KB = 8  # Si hay muy pocos chunks, inyectar todos directamente
    TOP_K_FALLBACK = 4  # Cuántos chunks inyectar si BM25 no puntúa nada

    # Colección pequeña → inyectar todo sin filtrar
    if len(chunks) <= MAX_SMALL_KB:
        merged = chunks
    else:
        # 1. BM25 (siempre)
        bm25_results = _bm25_retrieve(chunks, query)

        # 2. Embeddings (si hay modelo configurado)
        embed_model = (rules.get("knowledge_embed_model") or "").strip()
        embed_results = []
        if embed_model:
            hermes_cfg = _read_hermes_model_config()
            base_url = hermes_cfg.get("base_url", "")
            cache_path = Path(knowledge_dir) / "_embed_cache.pkl"
            embed_results = _embed_retrieve(chunks, query, embed_model, base_url, cache_path)

        # 3. Fusionar — embed primero (mayor prioridad), deduplicar por inicio del chunk
        seen: set = set()
        merged = []
        for fname, chunk in (embed_results + bm25_results):
            key = chunk[:120]
            if key not in seen:
                seen.add(key)
                merged.append((fname, chunk))

        # 4. Fallback: si ningún motor devolvió resultados, usar los N chunks más largos
        if not merged:
            sorted_by_len = sorted(chunks, key=lambda x: len(x[1]), reverse=True)
            merged = sorted_by_len[:TOP_K_FALLBACK]

    if not merged:
        return ""

    lines = ["[KNOWLEDGE BASE — Fragmentos relevantes para esta consulta]"]
    for fname, chunk in merged:
        lines.append(f"\n--- {fname} ---\n{chunk}")
    lines.append("[FIN KNOWLEDGE BASE]")
    return "\n".join(lines)


