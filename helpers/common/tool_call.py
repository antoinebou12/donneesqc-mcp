"""Exécution uniforme des tools MCP (erreurs ValueError vs génériques)."""

from __future__ import annotations

import logging
from typing import Any

from helpers.common.response import error

logger = logging.getLogger(__name__)


async def run_tool(
    label: str,
    action: Any,
    *,
    generic_error: str,
) -> str:
    """Exécute un tool et mappe les exceptions vers error(...).

    ValueError (validation SQL, params) conserve le message.
    Les autres exceptions sont journalisées avec un message générique.
    """
    try:
        return await action()
    except ValueError as exc:
        return error(str(exc))
    except Exception:
        logger.exception("Erreur dans %s", label)
        return error(generic_error)
