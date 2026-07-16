"""Tests Vercel / ASGI / config serverless."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _reload_config():
    import helpers.common.config as config

    return importlib.reload(config)


def test_local_defaults(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("MCP_STATELESS_HTTP", raising=False)
    monkeypatch.delenv("MCP_JSON_RESPONSE", raising=False)
    monkeypatch.delenv("DOWNLOAD_MAX_BYTES", raising=False)
    monkeypatch.delenv("HTTP_CACHE_MAX_ENTRIES", raising=False)
    monkeypatch.delenv("HTTP_CACHE_TTL_SECONDS", raising=False)

    config = _reload_config()
    assert config.IS_VERCEL is False
    assert config.MCP_STATELESS_HTTP is False
    assert config.MCP_JSON_RESPONSE is False
    assert config.DOWNLOAD_MAX_BYTES == 50 * 1024 * 1024
    assert config.HTTP_CACHE_MAX_ENTRIES == 256
    assert config.HTTP_CACHE_TTL_SECONDS == 60.0


def test_vercel_env_caps(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DOWNLOAD_MAX_BYTES", raising=False)
    monkeypatch.delenv("HTTP_CACHE_MAX_ENTRIES", raising=False)
    monkeypatch.delenv("HTTP_CACHE_TTL_SECONDS", raising=False)
    monkeypatch.delenv("MCP_STATELESS_HTTP", raising=False)
    monkeypatch.delenv("MCP_JSON_RESPONSE", raising=False)

    config = _reload_config()
    assert config.IS_VERCEL is True
    assert config.MCP_STATELESS_HTTP is True
    assert config.MCP_JSON_RESPONSE is True
    assert config.DOWNLOAD_MAX_BYTES == 5 * 1024 * 1024
    assert config.HTTP_CACHE_MAX_ENTRIES == 64
    assert config.HTTP_CACHE_TTL_SECONDS == 30.0

    monkeypatch.delenv("VERCEL", raising=False)
    _reload_config()


def test_mcp_stateless_flag_forces_mode(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.setenv("MCP_STATELESS_HTTP", "true")
    monkeypatch.setenv("MCP_JSON_RESPONSE", "yes")

    config = _reload_config()
    assert config.IS_VERCEL is False
    assert config.MCP_STATELESS_HTTP is True
    assert config.MCP_JSON_RESPONSE is True

    monkeypatch.delenv("MCP_STATELESS_HTTP", raising=False)
    monkeypatch.delenv("MCP_JSON_RESPONSE", raising=False)
    _reload_config()


def test_asgi_app_imports():
    import asgi

    assert asgi.app is not None
    assert callable(asgi.app)


def test_fastmcp_stateless_under_vercel_subprocess():
    """FastMCP est construit à l'import : vérifier dans un process isolé avec VERCEL=1."""
    code = (
        "from tools import mcp; assert mcp.settings.stateless_http is True; assert mcp.settings.json_response is True"
    )
    env = os.environ.copy()
    env["VERCEL"] = "1"
    env.pop("VERCEL_ENV", None)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
