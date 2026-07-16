"""Tests for smoke_report formatting and smoke_examples report lifecycle."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from smoke_report import format_body_section, format_step_markdown, md_table  # noqa: E402


def test_md_table_basic() -> None:
    text = md_table(["A", "B"], [["1", "2"], ["3", "4"]])
    assert "| A | B |" in text
    assert "| 1 | 2 |" in text


def test_format_body_top_orgs_has_table_and_ascii() -> None:
    body = {
        "total_organizations": 2,
        "total_datasets": 100,
        "top_organizations": [
            {"name": "Montréal", "datasets": 80},
            {"name": "Laval", "datasets": 20},
        ],
    }
    text = format_body_section(body)
    assert "Montréal" in text
    assert "```text" in text
    assert "█" in text


def test_format_body_events_table() -> None:
    body = {
        "events": [
            {
                "date": "2026-07-19",
                "category": "piknic",
                "venue_or_stage": "SCÈNE FIZZ",
                "artists": [{"name": "Mandragora", "time": "19H30"}],
            }
        ],
        "warning": None,
    }
    text = format_body_section(body)
    assert "Mandragora" in text
    assert "SCÈNE FIZZ" in text


def test_format_step_markdown_fail() -> None:
    text = format_step_markdown(
        number=3,
        title="qc_get_catalog_stats",
        status="FAIL",
        error="timeout",
    )
    assert "**Status:** FAIL" in text
    assert "timeout" in text


def test_report_deleted_on_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec = importlib.util.spec_from_file_location(
        "smoke_examples_ok",
        SCRIPTS / "smoke_examples.py",
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["smoke_examples_ok"] = mod
    spec.loader.exec_module(mod)

    async def ok_step() -> str:
        return '{"version": "0.0.0-test"}'

    monkeypatch.setattr(
        mod,
        "_build_steps",
        lambda: [mod.Step(1, "version", False, ok_step)],
    )

    import tempfile as tf

    real_mkstemp = tf.mkstemp

    def _mkstemp(*args, **kwargs):
        kwargs.setdefault("dir", str(tmp_path))
        return real_mkstemp(*args, **kwargs)

    monkeypatch.setattr(tf, "mkstemp", _mkstemp)
    monkeypatch.setattr(mod, "tempfile", tf)

    code = __import__("asyncio").run(mod._run(live=False, only={1}, keep_report=False))
    assert code == 0
    leftovers = list(tmp_path.glob("donneesqc-smoke-*.md"))
    assert leftovers == []


def test_report_kept_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec = importlib.util.spec_from_file_location(
        "smoke_examples_fail",
        SCRIPTS / "smoke_examples.py",
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["smoke_examples_fail"] = mod
    spec.loader.exec_module(mod)

    async def bad_step() -> str:
        return '{"error": "boom"}'

    monkeypatch.setattr(
        mod,
        "_build_steps",
        lambda: [mod.Step(1, "bad", False, bad_step)],
    )

    import tempfile as tf

    real_mkstemp = tf.mkstemp

    def _mkstemp(*args, **kwargs):
        kwargs.setdefault("dir", str(tmp_path))
        return real_mkstemp(*args, **kwargs)

    monkeypatch.setattr(tf, "mkstemp", _mkstemp)
    monkeypatch.setattr(mod, "tempfile", tf)

    code = __import__("asyncio").run(mod._run(live=False, only={1}, keep_report=False))
    assert code == 1
    leftovers = list(tmp_path.glob("donneesqc-smoke-*.md"))
    assert len(leftovers) == 1
    content = leftovers[0].read_text(encoding="utf-8")
    assert "FAIL" in content
    assert "boom" in content
