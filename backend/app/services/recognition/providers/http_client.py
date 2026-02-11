"""Unified HTTP client for external recognition providers with security controls."""

import asyncio
import logging
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with QPS and daily limits."""

    def __init__(self, qps: float = 1.0, daily_limit: int = 1000):
        """
        Initialize rate limiter.

        Args:
            qps: Queries per second (default: 1.0)
            daily_limit: Maximum queries per day (default: 1000)
        """
        self.qps = qps
        self.daily_limit = daily_limit
        self._request_times: deque[datetime] = deque()
        self._daily_count = 0
        self._daily_reset = datetime.now(UTC).date()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """
        Try to acquire a request slot.

        Returns:
            True if request allowed, False if rate limited
        """
        async with self._lock:
            now = datetime.now(UTC)
            today = now.date()

            # Reset daily counter if new day
            if today > self._daily_reset:
                self._daily_count = 0
                self._daily_reset = today

            # Check daily limit
            if self._daily_count >= self.daily_limit:
                logger.warning(
                    f"Daily limit reached: {self._daily_count}/{self.daily_limit}"
                )
                return False

            # Remove old request times (older than 1 second)
            cutoff = now - timedelta(seconds=1)
            while self._request_times and self._request_times[0] < cutoff:
                self._request_times.popleft()

            # Check QPS limit
            if len(self._request_times) >= self.qps:
                logger.warning(
                    f"QPS limit reached: {len(self._request_times)}/{self.qps}"
                )
                return False

            # Allow request
            self._request_times.append(now)
            self._daily_count += 1
            return True

    def get_stats(self) -> dict[str, Any]:
        """Get current rate limiter statistics."""
        return {
            "qps_limit": self.qps,
            "daily_limit": self.daily_limit,
            "daily_count": self._daily_count,
            "current_qps": len(self._request_times),
        }


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls in half-open state before closing
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._failure_count = 0
        self._last_failure_time: datetime | None = None
        self._state = "closed"  # closed, open, half_open
        self._half_open_success_count = 0
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self._state == "open":
                if self._last_failure_time:
                    elapsed = (
                        datetime.now(UTC) - self._last_failure_time
                    ).total_seconds()
                    if elapsed >= self.recovery_timeout:
                        self._state = "half_open"
                        self._half_open_success_count = 0
                        logger.info("Circuit breaker: entering half-open state")
                    else:
                        raise Exception(
                            f"Circuit breaker is OPEN. "
                            f"Retry after {self.recovery_timeout - int(elapsed)}s"
                        )

        try:
            result = await func(*args, **kwargs)
            # Success
            async with self._lock:
                if self._state == "half_open":
                    self._half_open_success_count += 1
                    if self._half_open_success_count >= self.half_open_max_calls:
                        self._state = "closed"
                        self._failure_count = 0
                        logger.info("Circuit breaker: closing (recovered)")
                elif self._state == "closed":
                    self._failure_count = 0
            return result
        except Exception as e:
            # Failure
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = datetime.now(UTC)
                if self._failure_count >= self.failure_threshold:
                    self._state = "open"
                    logger.error(
                        f"Circuit breaker: OPEN (failures: {self._failure_count})"
                    )
            raise e

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "last_failure_time": (
                self._last_failure_time.isoformat() if self._last_failure_time else None
            ),
        }


class SecureHTTPClient:
    """Secure HTTP client with domain whitelist, rate limiting, and circuit breaker."""

    def __init__(
        self,
        allowed_domains: list[str],
        timeout: float = 5.0,
        max_retries: int = 2,
        qps: float = 1.0,
        daily_limit: int = 1000,
    ):
        """
        Initialize secure HTTP client.

        Args:
            allowed_domains: List of allowed domain names (e.g., ["macvendors.com"])
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            qps: Queries per second limit
            daily_limit: Daily request limit
        """
        self.allowed_domains = set(domain.lower() for domain in allowed_domains)
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = RateLimiter(qps=qps, daily_limit=daily_limit)
        self.circuit_breaker = CircuitBreaker()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def _check_domain(self, url: str) -> bool:
        """
        Check if URL domain is in whitelist.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]
            return domain in self.allowed_domains
        except Exception as e:
            logger.error(f"Failed to parse URL {url}: {e}")
            return False

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform secure GET request.

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            HTTP response

        Raises:
            ValueError: If domain not whitelisted
            Exception: If rate limited or circuit breaker open
        """
        # Check domain whitelist
        if not self._check_domain(url):
            raise ValueError(f"Domain not in whitelist: {urlparse(url).netloc}")

        # Check rate limit
        if not await self.rate_limiter.acquire():
            raise Exception("Rate limit exceeded")

        # Execute with circuit breaker
        async def _do_request():
            client = await self._get_client()
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError:
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise
                except httpx.TimeoutException:
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise

        return await self.circuit_breaker.call(_do_request)

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform secure POST request.

        Args:
            url: Request URL
            json: JSON payload
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            ValueError: If domain not whitelisted
            Exception: If rate limited or circuit breaker open
        """
        # Check domain whitelist
        if not self._check_domain(url):
            raise ValueError(f"Domain not in whitelist: {urlparse(url).netloc}")

        # Check rate limit
        if not await self.rate_limiter.acquire():
            raise Exception("Rate limit exceeded")

        # Execute with circuit breaker
        async def _do_request():
            client = await self._get_client()
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(url, json=json, headers=headers)
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError:
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise
                except httpx.TimeoutException:
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise

        return await self.circuit_breaker.call(_do_request)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        return {
            "allowed_domains": list(self.allowed_domains),
            "rate_limiter": self.rate_limiter.get_stats(),
            "circuit_breaker": self.circuit_breaker.get_state(),
        }


def create_http_client_for_provider(provider_name: str) -> SecureHTTPClient:
    """
    Create HTTP client for a specific provider with appropriate limits.

    Args:
        provider_name: Provider name (e.g., "macvendors", "fingerbank")

    Returns:
        Configured SecureHTTPClient instance
    """
    # Provider-specific configurations
    provider_configs = {
        "macvendors": {
            "domains": ["macvendors.com", "api.macvendors.com"],
            "qps": 1.0,  # Conservative: 1 request per second
            "daily_limit": 1000,  # MACVendors free tier: 1000/day
            "timeout": 5.0,
        },
        "fingerbank": {
            "domains": ["api.fingerbank.org"],
            "qps": 0.5,  # More conservative for paid service
            "daily_limit": 500,
            "timeout": 10.0,
        },
    }

    config = provider_configs.get(provider_name.lower(), {})
    if not config:
        raise ValueError(f"Unknown provider: {provider_name}")

    return SecureHTTPClient(
        allowed_domains=config["domains"],
        timeout=config["timeout"],
        qps=config["qps"],
        daily_limit=config["daily_limit"],
    )
