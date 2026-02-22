"""Factories for active Embedder / VectorStore / Retrieval profiles."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from simple_rag.config.settings import get_settings, load_profiles
from simple_rag.embeddings.local_hf import LocalHFEmbedder
from simple_rag.embeddings.remote import RemoteEmbedder
from simple_rag.vectorstores.base import DistanceMetric, IndexSpec
from simple_rag.vectorstores.pgvector_store import PgVectorStore


def _get_active_profile(group: str) -> dict[str, Any]:
    profiles = load_profiles()
    group_data = profiles.get(group, {}) or {}
    active = group_data.get("active", "")
    conf = (group_data.get("profiles", {}) or {}).get(active, {}) or {}
    return {"active": active, "conf": conf, "group": group, "all": profiles}


def _resolve_env_placeholder(val: str | None, fallback: str) -> str:
    if not val:
        return fallback
    if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
        return fallback
    return val


_SAN_RE = re.compile(r"[^A-Za-z0-9_]+")


def sanitize_ident(s: str, *, max_len: int = 48) -> str:
    s = (s or "").strip()
    s = s.replace("/", "_").replace("-", "_")
    s = _SAN_RE.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "default"
    if s[0].isdigit():
        s = "m_" + s
    return s[:max_len]


@lru_cache
def get_embedder():
    p = _get_active_profile("embeddings")
    conf = p["conf"]
    provider = (conf.get("provider") or "").lower()

    if provider == "local_hf":
        return LocalHFEmbedder(
            model_name=conf.get("model", "BAAI/bge-m3"),
            batch_size=int(conf.get("batch_size", 16)),
            device=conf.get("device", "cpu"),
        )

    if provider in {"remote_openai_compatible", "remote"}:
        settings = get_settings()
        return RemoteEmbedder(
            base_url=conf.get("base_url", ""),
            model=conf.get("model", "text-embedding-3-large"),
            api_key=str(conf.get("api_key") or ""),
            dim=int(conf.get("dim", 1024)),
            timeout_s=float(conf.get("timeout_s", 10.0)),
            batch_size=int(conf.get("batch_size", 128)),
        )

    # Fallback
    return LocalHFEmbedder(model_name="BAAI/bge-m3", batch_size=16, device="cpu")


@lru_cache
def get_vector_store() -> PgVectorStore:
    p = _get_active_profile("vector_stores")
    conf = p["conf"]
    provider = (conf.get("provider") or "").lower()
    settings = get_settings()

    if provider == "pgvector":
        dsn = _resolve_env_placeholder(conf.get("dsn"), settings.pg_dsn)
        if dsn.startswith("postgresql://") and "+asyncpg" not in dsn:
            dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
        return PgVectorStore(dsn=dsn)

    # Fallback to pgvector
    return PgVectorStore(dsn=settings.pg_dsn)


@lru_cache
def get_vector_index_spec() -> IndexSpec:
    embedder = get_embedder()
    profiles = load_profiles()
    vs_group = profiles.get("vector_stores", {}) or {}
    active_vs = (vs_group.get("active") or "").strip()
    vs_conf = (vs_group.get("profiles", {}) or {}).get(active_vs, {}) or {}
    metric_str = (vs_conf.get("default_metric") or "cosine").lower()
    metric = DistanceMetric(metric_str) if metric_str in {m.value for m in DistanceMetric} else DistanceMetric.COSINE

    index_name = f"chunks__{sanitize_ident(embedder.model_id)}"
    return IndexSpec(
        name=index_name,
        dimension=int(embedder.dim),
        metric=metric,
        extra_params={"m": 16, "ef_construction": 64},
    )


def get_retrieval_profile(name_override: str | None = None) -> dict[str, Any]:
    profiles = load_profiles()
    group = profiles.get("retrieval", {}) or {}
    active = (name_override or group.get("active") or "").strip()
    conf = (group.get("profiles", {}) or {}).get(active, {}) or {}
    return {"name": active, "conf": conf}

