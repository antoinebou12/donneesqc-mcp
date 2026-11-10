"""Client HTTP async avec retry, rate limiting, cache TTL et support Retry-After."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any
from urllib.parse import urlparse

import httpx

from helpers.common.config import (
    DOWNLOAD_MAX_BYTES,
    HTTP_CACHE_MAX_ENTRIES,
    HTTP_CACHE_TTL_SECONDS,
    HTTP_MAX_RETRIES,
    HTTP_RATE_LIMIT_BURST,
    HTTP_RATE_LIMIT_RPS,
    HTTP_TIMEOUT,
    HTTP_USER_AGENT,
)

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


class _TokenBucket:
    """Token bucket asynchrone pour un hôte."""

    def __init__(self, rate: float, burst: float) -> None:
        self.rate = max(rate, 0.1)
        self.burst = max(burst, 1.0)
        self.tokens = self.burst
        self.updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.updated
                self.updated = now
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait)


_buckets: dict[str, _TokenBucket] = {}
_buckets_lock = asyncio.Lock()

# Cache GET: clé -> (expire_monotonic, value)
_cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
_cache_lock = asyncio.Lock()


async def _acquire_rate_limit(url: str) -> None:
    """Attend un jeton pour l'hôte de l'URL."""
    host = urlparse(url).netloc or "default"
    async with _buckets_lock:
        bucket = _buckets.get(host)
        if bucket is None:
            bucket = _TokenBucket(HTTP_RATE_LIMIT_RPS, HTTP_RATE_LIMIT_BURST)
            _buckets[host] = bucket
    await bucket.acquire()


def _cache_key(url: str, params: dict[str, Any] | None) -> str:
    raw = f"{url}?{sorted((params or {}).items())!s}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _cache_get(key: str) -> Any | None:
    async with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        expires, value = entry
        if time.monotonic() >= expires:
            del _cache[key]
            return None
        _cache.move_to_end(key)
        return value


async def _cache_set(key: str, value: Any) -> None:
    if HTTP_CACHE_TTL_SECONDS <= 0 or HTTP_CACHE_MAX_ENTRIES <= 0:
        return
    async with _cache_lock:
        expires = time.monotonic() + HTTP_CACHE_TTL_SECONDS
        _cache[key] = (expires, value)
        _cache.move_to_end(key)
        while len(_cache) > HTTP_CACHE_MAX_ENTRIES:
            _cache.popitem(last=False)


def clear_http_cache() -> None:
    """Vide le cache HTTP GET (utile pour les tests)."""
    _cache.clear()


def clear_rate_limiters() -> None:
    """Réinitialise les buckets de rate limit (utile pour les tests)."""
    _buckets.clear()


async def get_client() -> httpx.AsyncClient:
    global _client  # noqa: PLW0603
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(HTTP_TIMEOUT),
            headers={"User-Agent": HTTP_USER_AGENT},
            follow_redirects=True,
        )
    return _client


def _get_retry_after(response: httpx.Response) -> float | None:
    """Extrait le delai Retry-After d'une reponse 429."""
    header = response.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return float(header)
    except ValueError:
        return None


async def _retry(
    fn,
    *,
    url: str,
    params: dict[str, Any] | None = None,
) -> httpx.Response:
    """Execute une requete HTTP avec rate limit, retry, backoff et Retry-After."""
    last_error: Exception | None = None

    for attempt in range(HTTP_MAX_RETRIES):
        await _acquire_rate_limit(url)
        client = await get_client()
        try:
            resp = await fn(client, url, params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(
                "HTTP %s pour %s (tentative %d/%d)",
                e.response.status_code,
                url,
                attempt + 1,
                HTTP_MAX_RETRIES,
            )
            last_error = e

            # Respecter Retry-After sur 429
            if e.response.status_code == 429:
                retry_after = _get_retry_after(e.response)
                if retry_after is not None and attempt < HTTP_MAX_RETRIES - 1:
                    delay = min(retry_after, 60.0)  # cap a 60s
                    logger.info("429 Retry-After: %ss pour %s", delay, url)
                    await asyncio.sleep(delay)
                    continue

            if e.response.status_code < 500 and e.response.status_code != 429:
                raise
        except httpx.RequestError as e:
            logger.warning(
                "Erreur reseau pour %s (tentative %d/%d): %s",
                url,
                attempt + 1,
                HTTP_MAX_RETRIES,
                e,
            )
            last_error = e
        else:
            return resp

        # Backoff exponentiel : 1s, 2s, 4s...
        if attempt < HTTP_MAX_RETRIES - 1:
            delay = 2**attempt
            logger.debug("Retry dans %ds pour %s", delay, url)
            await asyncio.sleep(delay)

    msg = f"Echec apres {HTTP_MAX_RETRIES} tentatives pour {url}"
    raise RuntimeError(msg) from last_error


async def fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    *,
    use_cache: bool = True,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """GET JSON avec retry exponentiel et cache TTL optionnel."""
    key = _cache_key(url, params) if use_cache else ""
    if use_cache:
        cached = await _cache_get(key)
        if cached is not None:
            logger.debug("Cache hit JSON pour %s", url)
            return cached

    resp = await _retry(
        lambda client, u, p: client.get(u, params=p, headers=headers),
        url=url,
        params=params,
    )
    data = resp.json()
    if use_cache:
        await _cache_set(key, data)
    return data


async def fetch_text(
    url: str,
    params: dict[str, Any] | None = None,
    *,
    use_cache: bool = True,
    headers: dict[str, str] | None = None,
) -> str:
    """GET retournant du texte brut (XML, etc.) avec retry et cache optionnel."""
    key = _cache_key(url, params) if use_cache else ""
    if use_cache:
        cached = await _cache_get(key)
        if cached is not None:
            logger.debug("Cache hit text pour %s", url)
            return cached

    resp = await _retry(
        lambda client, u, p: client.get(u, params=p, headers=headers),
        url=url,
        params=params,
    )
    text = resp.text
    if use_cache:
        await _cache_set(key, text)
    return text


async def fetch_post_form(
    url: str,
    data: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> str:
    """POST application/x-www-form-urlencoded avec retry; retourne le corps texte."""

    async def _post(client: httpx.AsyncClient, u: str, _params: dict[str, Any] | None) -> httpx.Response:
        return await client.post(u, data=data, headers=headers)

    resp = await _retry(_post, url=url, params=None)
    return resp.text


async def fetch_bytes(
    url: str,
    *,
    max_bytes: int | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    """GET retournant des bytes bruts (CSV, XLSX, protobuf, etc.) avec limite de taille.

    Args:
        url: URL du fichier a telecharger.
        max_bytes: Taille maximale en octets (defaut: DOWNLOAD_MAX_BYTES).
        headers: En-tetes HTTP optionnels (ex. apiKey STM + Accept protobuf).

    Raises:
        RuntimeError: Si le fichier depasse la limite de taille.
    """
    limit = max_bytes or DOWNLOAD_MAX_BYTES
    await _acquire_rate_limit(url)
    client = await get_client()

    async with client.stream("GET", url, headers=headers) as resp:
        resp.raise_for_status()

        # Verifier Content-Length si disponible
        content_length = resp.headers.get("content-length")
        if content_length and int(content_length) > limit:
            msg = f"Fichier trop volumineux ({int(content_length)} octets > {limit} octets max)"
            raise RuntimeError(msg)

        chunks: list[bytes] = []
        total = 0
        async for chunk in resp.aiter_bytes(chunk_size=65536):
            total += len(chunk)
            if total > limit:
                msg = f"Fichier trop volumineux (> {limit} octets max)"
                raise RuntimeError(msg)
            chunks.append(chunk)

    return b"".join(chunks)


async def close() -> None:
    global _client  # noqa: PLW0603
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
