"""Rate limiter and resilient HTTP client for web ingestion.

Enforces polite request delays, randomized jitter, exponential backoff,
and error handling.
"""

import time
import random
import logging
from typing import Optional, Dict, Any
import httpx

from src.config import SETTINGS

logger = logging.getLogger("ingestion.rate_limiter")


class ResilientHttpClient:
    """HTTP Client with built-in rate limiting and retry logic."""

    def __init__(
        self,
        base_delay: float = 1.0,
        jitter: float = 0.3,
        max_retries: int = 5,
        timeout: float = 30.0,
        user_agent: Optional[str] = None,
    ):
        crawler_cfg = SETTINGS.get("crawler", {})
        self.base_delay = base_delay or crawler_cfg.get("delay_seconds", 1.0)
        self.jitter = jitter or crawler_cfg.get("jitter_seconds", 0.3)
        self.max_retries = max_retries or crawler_cfg.get("max_retries", 5)
        self.timeout = timeout or crawler_cfg.get("timeout_seconds", 30.0)
        self.user_agent = user_agent or crawler_cfg.get(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        self._last_request_time: float = 0.0

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.client = httpx.Client(
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
        )

    def _wait_for_rate_limit(self) -> None:
        """Enforce rate limiting delay between consecutive requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        target_delay = self.base_delay + random.uniform(-self.jitter, self.jitter)
        target_delay = max(0.2, target_delay)

        if elapsed < target_delay:
            sleep_time = target_delay - elapsed
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Execute a rate-limited GET request with exponential backoff on errors."""
        attempt = 0
        last_exception = None

        while attempt < self.max_retries:
            attempt += 1
            self._wait_for_rate_limit()

            try:
                response = self.client.get(url, **kwargs)
                if response.status_code == 429 or response.status_code >= 500:
                    backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(
                        "Received HTTP %d for %s (attempt %d/%d). Backing off for %.2fs...",
                        response.status_code,
                        url,
                        attempt,
                        self.max_retries,
                        backoff,
                    )
                    time.sleep(backoff)
                    continue

                return response

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_exception = exc
                backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                logger.warning(
                    "Network error %s on %s (attempt %d/%d). Retrying in %.2fs...",
                    exc,
                    url,
                    attempt,
                    self.max_retries,
                    backoff,
                )
                time.sleep(backoff)

        if last_exception:
            raise last_exception
        raise httpx.HTTPStatusError(
            f"Failed after {self.max_retries} attempts: {url}",
            request=httpx.Request("GET", url),
            response=response,
        )

    def close(self) -> None:
        """Close the underlying HTTP client session."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
