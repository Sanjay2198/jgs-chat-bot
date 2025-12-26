"""
Helpers for creating Chroma clients (sync and async) using env vars.

Usage:
    from api.chroma_client import get_client, get_async_client

    client = get_client()  # defaults to localhost:8000 if no env vars set

    async def main():
        async_client = await get_async_client()
        ...
"""

import os
from urllib.parse import urlparse

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.async_api import AsyncClientAPI
from chromadb.config import Settings
from dotenv import load_dotenv

# Load .env so CHROMA_* variables are picked up when running locally.
load_dotenv()


def _bool_from_env(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.lower() in {"1", "true", "yes", "y", "on"}


def _resolve_connection_kwargs() -> dict:
    host_env = os.getenv("CHROMA_HOST", "localhost")
    port_env = os.getenv("CHROMA_PORT")
    ssl_env = _bool_from_env(os.getenv("CHROMA_SSL"))

    api_key = os.getenv("CHROMA_API_KEY") or os.getenv("CHROMADB_API_KEY")
    tenant = os.getenv("CHROMA_TENANT") or os.getenv("CHROMADB_TENANT")
    database = os.getenv("CHROMA_DATABASE") or os.getenv("CHROMADB_DATABASE") or "default"

    ssl = None
    host = host_env
    port = None

    # Allow users to pass a full URL (http/https) or just a host.
    if host_env.startswith("http://") or host_env.startswith("https://"):
        parsed = urlparse(host_env)
        host = parsed.hostname or host_env
        port = parsed.port
        ssl = parsed.scheme == "https"

    if port_env:
        try:
            port = int(port_env)
        except ValueError as exc:
            raise ValueError("CHROMA_PORT must be an integer") from exc

    if port is None:
        port = 8000 if host in {"localhost", "127.0.0.1"} else 443

    if ssl_env is not None:
        ssl = ssl_env
    if ssl is None:
        ssl = False if host in {"localhost", "127.0.0.1"} else True

    headers = None
    settings = None
    if api_key:
        headers = {"X-Chroma-Token": api_key, "Authorization": f"Bearer {api_key}"}
        settings = Settings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=api_key,
            chroma_auth_token_transport_header="X-Chroma-Token",
        )

    return {
        "host": host,
        "port": port,
        "ssl": ssl,
        "headers": headers,
        "tenant": tenant,
        "database": database,
        "settings": settings,
    }


def get_client(**overrides) -> ClientAPI:
    """
    Build a configured chromadb.HttpClient. Override any field via kwargs,
    e.g. get_client(host="localhost", port=8000, ssl=False).
    """
    cfg = _resolve_connection_kwargs()
    cfg.update({k: v for k, v in overrides.items() if v is not None})
    allowed_keys = ("host", "port", "ssl", "headers", "tenant", "database", "settings")
    safe_kwargs = {k: cfg[k] for k in allowed_keys if cfg.get(k) is not None}
    return chromadb.HttpClient(**safe_kwargs)


async def get_async_client(**overrides) -> AsyncClientAPI:
    """
    Build a configured chromadb.AsyncHttpClient. Same overrides as get_client.
    """
    cfg = _resolve_connection_kwargs()
    cfg.update({k: v for k, v in overrides.items() if v is not None})
    allowed_keys = ("host", "port", "ssl", "headers", "tenant", "database", "settings")
    safe_kwargs = {k: cfg[k] for k in allowed_keys if cfg.get(k) is not None}
    return await chromadb.AsyncHttpClient(**safe_kwargs)


__all__ = ["get_client", "get_async_client"]
