import re

import pytest
from stealth_requests import StealthSession, AsyncStealthSession
from stealth_requests import session as session_module
from stealth_requests.session import (
    CHROME_VERSION,
    IMPERSONATE,
    PLATFORM,
    PLATFORM_HINT,
    identity,
    impersonated_chrome_version,
)


URL = 'https://httpbin.org'

UA_PATTERN = re.compile(
    r'Mozilla/5\.0 \((?P<platform>[^)]+)\) AppleWebKit/537\.36 '
    r'\(KHTML, like Gecko\) Chrome/(?P<version>\d+)\.0\.0\.0 Safari/537\.36'
)


# --- The generated identity on its own ---


def test_impersonates_the_newest_chrome_curl_cffi_ships():
    assert IMPERSONATE == 'chrome'


def test_version_resolves_to_the_alias_target():
    from curl_cffi.requests.impersonate import REAL_TARGET_MAP

    assert impersonated_chrome_version() is not None
    assert REAL_TARGET_MAP['chrome'] == f'chrome{CHROME_VERSION}'


def test_platform_is_the_token_chrome_sends_on_every_mac():
    assert PLATFORM == 'Macintosh; Intel Mac OS X 10_15_7'
    assert PLATFORM_HINT == '"macOS"'


def test_identity_is_self_consistent():
    headers = identity()
    match = UA_PATTERN.fullmatch(headers['User-Agent'])

    assert match, f'not a real Chrome UA: {headers["User-Agent"]}'
    assert match.group('platform') == PLATFORM
    assert int(match.group('version')) == CHROME_VERSION
    assert headers['Sec-CH-UA-Platform'] == PLATFORM_HINT


def test_identity_is_empty_when_the_version_cannot_be_resolved(monkeypatch):
    monkeypatch.setattr(session_module, 'CHROME_VERSION', None)
    assert identity() == {}


# --- What actually reaches the server ---


def _assert_consistent(headers):
    match = UA_PATTERN.fullmatch(headers['User-Agent'])
    assert match, f'not a real Chrome UA: {headers["User-Agent"]}'
    assert match.group('platform') == PLATFORM
    assert headers['Sec-Ch-Ua-Platform'] == PLATFORM_HINT
    # Brand hints come from curl_cffi, so this catches the UA drifting from the TLS fp.
    assert f'"{CHROME_VERSION}"' in headers['Sec-Ch-Ua']


def test_sent_headers_are_consistent():
    with StealthSession() as s:
        _assert_consistent(s.get(f'{URL}/headers', retry=2).json()['headers'])


@pytest.mark.asyncio
async def test_async_sent_headers_are_consistent():
    async with AsyncStealthSession() as s:
        resp = await s.get(f'{URL}/headers', retry=2)
        _assert_consistent(resp.json()['headers'])


def test_only_macintosh_user_agents_are_ever_sent():
    for _ in range(5):
        with StealthSession() as s:
            ua = s.get(f'{URL}/headers', retry=2).json()['headers']['User-Agent']
        assert 'Macintosh' in ua, ua


def test_unresolvable_version_leaves_curl_cffi_headers_intact(monkeypatch):
    monkeypatch.setattr(session_module, 'CHROME_VERSION', None)

    with StealthSession() as s:
        headers = s.get(f'{URL}/headers', retry=2).json()['headers']

    # curl_cffi's own UA, not one we built - still macOS.
    assert UA_PATTERN.fullmatch(headers['User-Agent'])
    assert 'Macintosh' in headers['User-Agent']


def test_identity_is_stable_within_a_session():
    with StealthSession() as s:
        sent = [s.get(f'{URL}/headers', retry=2).json()['headers'] for _ in range(3)]

    assert len({h['User-Agent'] for h in sent}) == 1
    assert len({h['Sec-Ch-Ua-Platform'] for h in sent}) == 1


def test_caller_can_override_the_user_agent():
    with StealthSession(headers={'User-Agent': 'custom-agent/1.0'}) as s:
        headers = s.get(f'{URL}/headers', retry=2).json()['headers']

    assert headers['User-Agent'] == 'custom-agent/1.0'
