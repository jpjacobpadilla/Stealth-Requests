import re
import time
import random
import asyncio
from urllib.parse import urlparse, urlunparse
from functools import partialmethod

from .response import StealthResponse

from curl_cffi.requests.session import Session, AsyncSession, HttpMethod


RETRY_DELAY = 2  # Seconds
RETRYABLE_STATUS_CODES = {
    408,  # Request Timeout
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
    520,  # Cloudflare Unknown Error
    521,  # Cloudflare Web Server Is Down
    522,  # Cloudflare Connection Timed Out
    523,  # Cloudflare Origin Is Unreachable
    524,  # Cloudflare A Timeout Occurred
}


# curl_cffi resolves 'chrome' to the newest Chrome it ships.
IMPERSONATE = 'chrome'


def impersonated_chrome_version() -> int | None:
    # REAL_TARGET_MAP is private, so fall back to None if it ever moves.
    try:
        from curl_cffi.requests.impersonate import REAL_TARGET_MAP

        match = re.search(r'\d+', REAL_TARGET_MAP[IMPERSONATE])
        return int(match.group()) if match else None
    except Exception:
        return None


CHROME_VERSION = impersonated_chrome_version()

# The only platform tokens Chrome sends, each with its Sec-CH-UA-Platform value.
PLATFORMS = [
    ('Windows NT 10.0; Win64; x64', '"Windows"'),
    ('Macintosh; Intel Mac OS X 10_15_7', '"macOS"'),
    ('X11; Linux x86_64', '"Linux"'),
]

# Rough desktop Chrome split.
PLATFORM_WEIGHTS = (72, 21, 7)


def random_identity() -> dict[str, str]:
    # Without a known version, leave curl_cffi's own consistent headers alone.
    if CHROME_VERSION is None:
        return {}

    platform, ch_platform = random.choices(PLATFORMS, weights=PLATFORM_WEIGHTS)[0]
    user_agent = (
        f'Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36'
    )
    return {'User-Agent': user_agent, 'Sec-CH-UA-Platform': ch_platform}


class BaseStealthSession:
    def __init__(self, **kwargs):
        timeout = kwargs.pop('timeout', 30)

        headers = kwargs.pop('headers', {})
        for header, value in random_identity().items():
            headers.setdefault(header, value)

        self.last_request_url = None

        super().__init__(impersonate=IMPERSONATE, timeout=timeout, headers=headers, **kwargs)


class StealthSession(BaseStealthSession, Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def request(self, method: HttpMethod, url: str, *args, retry: int = 0, **kwargs) -> StealthResponse:
        assert retry >= 0

        referer = {'Referer': self.last_request_url} if self.last_request_url else {}
        extra_headers = referer | kwargs.pop('headers', {})

        start = time.perf_counter()
        for attempt in range(retry + 1):
            resp = super().request(method, url, *args, headers=extra_headers, **kwargs)

            if resp.status_code not in RETRYABLE_STATUS_CODES or attempt == retry:
                break

            # Retry after delay
            time.sleep(RETRY_DELAY)
        elapsed = time.perf_counter() - start

        parsed = urlparse(url)
        self.last_request_url = urlunparse(parsed._replace(query='', fragment=''))

        return StealthResponse(resp, elapsed)

    head = partialmethod(request, 'HEAD')
    get = partialmethod(request, 'GET')
    post = partialmethod(request, 'POST')
    put = partialmethod(request, 'PUT')
    patch = partialmethod(request, 'PATCH')
    delete = partialmethod(request, 'DELETE')
    options = partialmethod(request, 'OPTIONS')


class AsyncStealthSession(BaseStealthSession, AsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def request(self, method: HttpMethod, url: str, *args, retry: int = 0, **kwargs) -> StealthResponse:
        assert retry >= 0

        referer = {'Referer': self.last_request_url} if self.last_request_url else {}
        extra_headers = referer | kwargs.pop('headers', {})

        start = time.perf_counter()
        for attempt in range(retry + 1):
            resp = await super().request(method, url, *args, headers=extra_headers, **kwargs)

            if resp.status_code not in RETRYABLE_STATUS_CODES or attempt == retry:
                break

            # Retry after delay
            await asyncio.sleep(RETRY_DELAY)
        elapsed = time.perf_counter() - start

        parsed = urlparse(url)
        self.last_request_url = urlunparse(parsed._replace(query='', fragment=''))

        return StealthResponse(resp, elapsed)

    head = partialmethod(request, 'HEAD')
    get = partialmethod(request, 'GET')
    post = partialmethod(request, 'POST')
    put = partialmethod(request, 'PUT')
    patch = partialmethod(request, 'PATCH')
    delete = partialmethod(request, 'DELETE')
    options = partialmethod(request, 'OPTIONS')
