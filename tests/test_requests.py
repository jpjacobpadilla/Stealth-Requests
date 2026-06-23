import re
from unittest.mock import MagicMock, patch

import pytest

import stealth_requests as stealth
from stealth_requests import AsyncStealthSession, StealthSession

URL = 'https://httpbin.org'


# --- Sync ---


def test_get():
    resp = stealth.get(f'{URL}/get')
    assert resp.status_code == 200


def test_post():
    resp = stealth.post(f'{URL}/post', json={'key': 'value'})
    assert resp.status_code == 200
    assert resp.json()['json']['key'] == 'value'


def test_session_get():
    with StealthSession() as s:
        resp = s.get(f'{URL}/get')
        assert resp.status_code == 200


def test_session_sets_referer():
    with StealthSession() as s:
        s.get(f'{URL}/get')
        resp = s.get(f'{URL}/headers')
        headers = resp.json()['headers']
        assert f'{URL}/get' in headers.get('Referer', '')


def test_session_has_user_agent():
    with StealthSession() as s:
        resp = s.get(f'{URL}/headers')
        headers = resp.json()['headers']
        assert 'User-Agent' in headers
        assert headers['User-Agent'] != ''


# --- Async ---


@pytest.mark.asyncio
async def test_async_get():
    async with AsyncStealthSession() as s:
        resp = await s.get(f'{URL}/get')
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_async_post():
    async with AsyncStealthSession() as s:
        resp = await s.post(f'{URL}/post', json={'hello': 'world'})
        assert resp.status_code == 200
        assert resp.json()['json']['hello'] == 'world'


@pytest.mark.asyncio
async def test_async_session_sets_referer():
    async with AsyncStealthSession() as s:
        await s.get(f'{URL}/get')
        resp = await s.get(f'{URL}/headers')
        headers = resp.json()['headers']
        assert f'{URL}/get' in headers.get('Referer', '')


# --- Response features (using a real HTML page) ---

HTML_URL = 'https://books.toscrape.com'


def test_repr():
    resp = stealth.get(f'{URL}/get')
    assert re.fullmatch(r'<StealthResponse \[Status: \d+ Elapsed Time: \d+\.\d+ seconds\]>', repr(resp))


def test_links():
    resp = stealth.get(HTML_URL)
    assert isinstance(resp.links, tuple)
    assert len(resp.links) > 0
    assert all(isinstance(link, str) for link in resp.links)


def test_images():
    resp = stealth.get(HTML_URL)
    assert isinstance(resp.images, tuple)
    assert len(resp.images) > 0
    assert all(isinstance(img, str) for img in resp.images)


def test_emails():
    resp = stealth.get(HTML_URL)
    assert isinstance(resp.emails, tuple)
    if resp.emails:
        assert all('@' in e for e in resp.emails)


def test_phone_numbers():
    resp = stealth.get(HTML_URL)
    assert isinstance(resp.phone_numbers, tuple)
    if resp.phone_numbers:
        assert all(any(c.isdigit() for c in p) for p in resp.phone_numbers)


def test_metadata():
    resp = stealth.get(HTML_URL)
    meta = resp.meta
    assert isinstance(meta.title, str) and len(meta.title) > 0
    assert isinstance(meta.description, (str, type(None)))
    assert isinstance(meta.thumbnail, (str, type(None)))
    assert isinstance(meta.author, (str, type(None)))
    assert isinstance(meta.keywords, (tuple, type(None)))
    assert isinstance(meta.twitter_handle, (str, type(None)))
    assert isinstance(meta.robots, (tuple, type(None)))
    assert isinstance(meta.canonical, (str, type(None)))


# --- Retry ---


def _mock_response(status_code, url='https://example.com'):
    resp = MagicMock()
    resp.status_code = status_code
    resp.url = url
    resp.content = b''
    resp.text = ''
    resp.headers = {}
    return resp


class TestRetry:
    def test_no_retry_on_success(self):
        mock = _mock_response(200)
        with patch('stealth_requests.session.Session.request', return_value=mock):
            with StealthSession() as s:
                resp = s.get('https://example.com', retry=0)
        assert resp.status_code == 200

    def test_no_retry_on_non_retryable(self):
        mock = _mock_response(404)
        with patch('stealth_requests.session.Session.request', return_value=mock):
            with StealthSession() as s:
                resp = s.get('https://example.com', retry=1)
        assert resp.status_code == 404

    def test_retries_on_retryable_status(self):
        responses = [_mock_response(503), _mock_response(200)]
        with (
            patch('stealth_requests.session.Session.request', side_effect=responses),
            patch('stealth_requests.session.time.sleep'),
        ):
            with StealthSession() as s:
                resp = s.get('https://example.com', retry=1)
        assert resp.status_code == 200

    def test_retry_exhausted(self):
        responses = [_mock_response(503), _mock_response(503), _mock_response(503)]
        with (
            patch('stealth_requests.session.Session.request', side_effect=responses),
            patch('stealth_requests.session.time.sleep'),
        ):
            with StealthSession() as s:
                resp = s.get('https://example.com', retry=2)
        assert resp.status_code == 503
