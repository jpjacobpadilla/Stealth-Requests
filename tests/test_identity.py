import random
import re

import pytest
from stealth_requests import StealthSession, AsyncStealthSession
from stealth_requests import session as session_module
from stealth_requests.session import (
    CHROME_VERSION,
    IMPERSONATE,
    PLATFORMS,
    impersonated_chrome_version,
    random_identity,
)


URL = 'https://httpbin.org'

PLATFORM_HINTS = dict(PLATFORMS)

# Chrome's reduced User-Agent: a frozen platform token and a MAJOR.0.0.0 version.
UA_PATTERN = re.compile(
    r'Mozilla/5\.0 \((?P<platform>[^)]+)\) AppleWebKit/537\.36 '
    r'\(KHTML, like Gecko\) Chrome/(?P<version>\d+)\.0\.0\.0 Safari/537\.36'
)


# --- The generated identity on its own ---


def test_impersonates_the_newest_chrome_curl_cffi_ships():
    # The bare alias is the point: pinning a version here would go stale.
    assert IMPERSONATE == 'chrome'


def test_version_resolves_to_the_alias_target():
    from curl_cffi.requests.impersonate import REAL_TARGET_MAP

    assert impersonated_chrome_version() is not None
    assert REAL_TARGET_MAP['chrome'] == f'chrome{CHROME_VERSION}'


def test_identity_is_empty_when_the_version_cannot_be_resolved(monkeypatch):
    # curl_cffi's table is private, so the unresolvable path has to stay safe:
    # no overrides at all, rather than a version that might contradict the TLS
    # fingerprint.
    monkeypatch.setattr(session_module, 'CHROME_VERSION', None)
    assert random_identity() == {}


def test_unresolvable_version_leaves_curl_cffi_headers_intact(monkeypatch):
    monkeypatch.setattr(session_module, 'CHROME_VERSION', None)

    with StealthSession() as s:
        headers = s.get(f'{URL}/headers', retry=2).json()['headers']

    # Still a real Chrome UA, just curl_cffi's own rather than one we built.
    assert UA_PATTERN.fullmatch(headers['User-Agent'])


@pytest.mark.parametrize('_', range(50))
def test_identity_is_self_consistent(_):
    identity = random_identity()
    match = UA_PATTERN.fullmatch(identity['User-Agent'])

    assert match, f'not a real Chrome UA: {identity["User-Agent"]}'
    assert int(match.group('version')) == CHROME_VERSION
    assert identity['Sec-CH-UA-Platform'] == PLATFORM_HINTS[match.group('platform')]


def test_every_platform_token_is_one_chrome_actually_sends():
    assert set(PLATFORM_HINTS) == {
        'Windows NT 10.0; Win64; x64',
        'Macintosh; Intel Mac OS X 10_15_7',
        'X11; Linux x86_64',
    }


def test_identity_rotates_between_sessions():
    # Seeded so a rare sample that happens to miss the least-weighted platform
    # can't fail the suite.
    state = random.getstate()
    random.seed(0)
    try:
        agents = {random_identity()['User-Agent'] for _ in range(200)}
    finally:
        random.setstate(state)

    assert len(agents) == len(PLATFORMS)


# --- What actually reaches the server ---


def _assert_consistent(headers):
    match = UA_PATTERN.fullmatch(headers['User-Agent'])
    assert match, f'not a real Chrome UA: {headers["User-Agent"]}'
    assert headers['Sec-Ch-Ua-Platform'] == PLATFORM_HINTS[match.group('platform')]
    # The brand hints come from curl_cffi's impersonation profile, so this is what
    # catches the UA drifting away from the TLS fingerprint.
    assert f'"{CHROME_VERSION}"' in headers['Sec-Ch-Ua']


def test_sent_headers_are_consistent():
    with StealthSession() as s:
        _assert_consistent(s.get(f'{URL}/headers', retry=2).json()['headers'])


@pytest.mark.asyncio
async def test_async_sent_headers_are_consistent():
    async with AsyncStealthSession() as s:
        resp = await s.get(f'{URL}/headers', retry=2)
        _assert_consistent(resp.json()['headers'])


def test_identity_is_stable_within_a_session():
    with StealthSession() as s:
        sent = [s.get(f'{URL}/headers', retry=2).json()['headers'] for _ in range(3)]

    assert len({h['User-Agent'] for h in sent}) == 1
    assert len({h['Sec-Ch-Ua-Platform'] for h in sent}) == 1


def test_caller_can_override_the_user_agent():
    with StealthSession(headers={'User-Agent': 'custom-agent/1.0'}) as s:
        headers = s.get(f'{URL}/headers', retry=2).json()['headers']

    assert headers['User-Agent'] == 'custom-agent/1.0'
