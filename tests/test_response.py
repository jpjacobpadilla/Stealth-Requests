from types import SimpleNamespace
from unittest.mock import patch

import pytest

from stealth_requests.response import StealthResponse


def make_response(html, url='https://example.com'):
    """Create a StealthResponse from raw HTML and a fake URL."""
    raw = SimpleNamespace(
        content=html.encode(),
        text=html,
        url=url,
        status_code=200,
    )
    return StealthResponse(raw, elapsed=0.1)


# ── Tables ──────────────────────────────────────────────────────────────


class TestTables:
    def test_basic_thead_tbody(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Name</th><th>Age</th></tr></thead>
            <tbody>
                <tr><td>Alice</td><td>30</td></tr>
                <tr><td>Bob</td><td>25</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'Name': ['Alice', 'Bob'], 'Age': ['30', '25']}]

    def test_table_without_thead(self):
        html = """
        <html><body>
        <table>
            <tr><th>Color</th><th>Hex</th></tr>
            <tr><td>Red</td><td>#FF0000</td></tr>
            <tr><td>Blue</td><td>#0000FF</td></tr>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'Color': ['Red', 'Blue'], 'Hex': ['#FF0000', '#0000FF']}]

    def test_multiple_tables(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>X</th></tr></thead>
            <tbody><tr><td>1</td></tr></tbody>
        </table>
        <table>
            <thead><tr><th>Y</th></tr></thead>
            <tbody><tr><td>2</td></tr></tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert len(resp.tables) == 2
        assert resp.tables[0] == {'X': ['1']}
        assert resp.tables[1] == {'Y': ['2']}

    def test_table_no_headers_skipped(self):
        html = """
        <html><body>
        <table>
            <tr><td>no</td><td>headers</td></tr>
            <tr><td>at</td><td>all</td></tr>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == []

    def test_table_empty_headers_skipped(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th></th><th></th></tr></thead>
            <tbody><tr><td>a</td><td>b</td></tr></tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == []

    def test_row_with_fewer_cells(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>A</th><th>B</th><th>C</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>2</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'A': ['1'], 'B': ['2'], 'C': ['']}]

    def test_tables_cached(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Col</th></tr></thead>
            <tbody><tr><td>val</td></tr></tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        first = resp.tables
        second = resp.tables
        assert first is second

    def test_no_tables(self):
        html = '<html><body><p>No tables here</p></body></html>'
        resp = make_response(html)
        assert resp.tables == []

    def test_nested_elements_in_cells(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Link</th><th>Info</th></tr></thead>
            <tbody>
                <tr><td><a href="/page">Click here</a></td><td><strong>Bold</strong> text</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'Link': ['Click here'], 'Info': ['Bold text']}]

    def test_whitespace_in_cells(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>  Name  </th><th>  Value  </th></tr></thead>
            <tbody>
                <tr><td>  foo  </td><td>  bar  </td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'Name': ['foo'], 'Value': ['bar']}]

    def test_single_column_table(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Items</th></tr></thead>
            <tbody>
                <tr><td>Apple</td></tr>
                <tr><td>Banana</td></tr>
                <tr><td>Cherry</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'Items': ['Apple', 'Banana', 'Cherry']}]

    def test_many_columns(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td></tr>
                <tr><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'A': ['1', '6'], 'B': ['2', '7'], 'C': ['3', '8'], 'D': ['4', '9'], 'E': ['5', '10']}]

    def test_empty_tbody(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Name</th><th>Age</th></tr></thead>
            <tbody></tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == [{'Name': [], 'Age': []}]

    def test_mixed_valid_and_invalid_tables(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Good</th></tr></thead>
            <tbody><tr><td>yes</td></tr></tbody>
        </table>
        <table>
            <tr><td>no</td><td>headers</td></tr>
        </table>
        <table>
            <thead><tr><th>Also Good</th></tr></thead>
            <tbody><tr><td>yep</td></tr></tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert len(resp.tables) == 2
        assert resp.tables[0] == {'Good': ['yes']}
        assert resp.tables[1] == {'Also Good': ['yep']}

    def test_row_with_extra_cells(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>A</th><th>B</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>2</td><td>3</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        # Extra cells beyond the header count are ignored
        assert resp.tables == [{'A': ['1'], 'B': ['2']}]

    def test_special_characters_in_cells(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Symbol</th><th>Price</th></tr></thead>
            <tbody>
                <tr><td>AT&amp;T</td><td>$25.50</td></tr>
                <tr><td>O'Reilly</td><td>&euro;30.00</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables[0]['Symbol'] == ['AT&T', "O'Reilly"]
        assert resp.tables[0]['Price'] == ['$25.50', '\u20ac30.00']

    def test_nested_table_parsed_separately(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Outer</th></tr></thead>
            <tbody>
                <tr><td>
                    <table>
                        <thead><tr><th>Inner</th></tr></thead>
                        <tbody><tr><td>nested</td></tr></tbody>
                    </table>
                </td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        # Both the outer and inner table should be parsed
        assert len(resp.tables) == 2
        outer = next(t for t in resp.tables if 'Outer' in t)
        # Outer table must have exactly 1 row (no inner table rows leaked in)
        assert len(outer['Outer']) == 1
        inner = next(t for t in resp.tables if 'Inner' in t)
        assert inner == {'Inner': ['nested']}

    def test_malformed_missing_td_skipped(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>A</th><th>B</th></tr></thead>
            <tbody>
                <tr></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        # Row with zero cells — both columns get empty strings
        assert resp.tables == [{'A': [''], 'B': ['']}]

    def test_malformed_empty_table_tag(self):
        html = '<html><body><table></table></body></html>'
        resp = make_response(html)
        assert resp.tables == []

    def test_malformed_thead_no_th(self):
        html = """
        <html><body>
        <table>
            <thead><tr></tr></thead>
            <tbody><tr><td>data</td></tr></tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        assert resp.tables == []

    def test_malformed_unclosed_tags(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>X</th><th>Y</th></tr></thead>
            <tbody>
                <tr><td>1<td>2</tr>
                <tr><td>3</td><td>4</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        resp = make_response(html)
        # lxml fixes up the broken HTML — table should still parse
        assert len(resp.tables) == 1
        assert resp.tables[0]['X'] == ['1', '3']

    def test_malformed_only_thead_no_tbody(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>Header</th></tr></thead>
        </table>
        </body></html>
        """
        resp = make_response(html)
        # Headers exist but no data rows
        assert resp.tables == [{'Header': []}]


# ── Metadata ────────────────────────────────────────────────────────────


class TestMetadata:
    def test_all_meta_fields(self):
        html = """
        <html><head>
            <title>Test Page</title>
            <meta name="description" content="A test page">
            <meta property="og:image" content="https://example.com/img.png">
            <meta name="author" content="Alice">
            <meta name="keywords" content="python, scraping">
            <meta name="twitter:site" content="@alice">
            <meta name="robots" content="index, follow">
            <link rel="canonical" href="https://example.com/canonical">
        </head><body></body></html>
        """
        resp = make_response(html)
        meta = resp.meta
        assert meta.title == 'Test Page'
        assert meta.description == 'A test page'
        assert meta.thumbnail == 'https://example.com/img.png'
        assert meta.author == 'Alice'
        assert meta.keywords == ('python', 'scraping')
        assert meta.twitter_handle == '@alice'
        assert meta.robots == ('index', 'follow')
        assert meta.canonical == 'https://example.com/canonical'

    def test_missing_meta_fields(self):
        html = '<html><head></head><body></body></html>'
        resp = make_response(html)
        meta = resp.meta
        assert meta.title is None
        assert meta.description is None
        assert meta.thumbnail is None
        assert meta.author is None
        assert meta.keywords is None
        assert meta.twitter_handle is None
        assert meta.robots is None
        assert meta.canonical is None

    def test_meta_cached(self):
        html = '<html><head><title>Hi</title></head><body></body></html>'
        resp = make_response(html)
        first = resp.meta
        second = resp.meta
        assert first is second


# ── Emails ──────────────────────────────────────────────────────────────


class TestEmails:
    def test_extracts_emails(self):
        html = '<html><body>Contact us at info@example.com or support@test.org</body></html>'
        resp = make_response(html)
        assert set(resp.emails) == {'info@example.com', 'support@test.org'}

    def test_no_emails(self):
        html = '<html><body>No emails here</body></html>'
        resp = make_response(html)
        assert resp.emails == ()

    def test_deduplicates_emails(self):
        html = '<html><body>a@b.com and a@b.com again</body></html>'
        resp = make_response(html)
        assert resp.emails == ('a@b.com',)


# ── Phone Numbers ───────────────────────────────────────────────────────


class TestPhoneNumbers:
    def test_standard_formats(self):
        html = '<html><body>(800) 123-4567 and 212-555-7890</body></html>'
        resp = make_response(html)
        assert '(800) 123-4567' in resp.phone_numbers
        assert '212-555-7890' in resp.phone_numbers

    def test_with_country_code(self):
        html = '<html><body>+1 800-123-4567</body></html>'
        resp = make_response(html)
        assert len(resp.phone_numbers) == 1

    def test_no_phone_numbers(self):
        html = '<html><body>No phones</body></html>'
        resp = make_response(html)
        assert resp.phone_numbers == ()


# ── Links ───────────────────────────────────────────────────────────────


class TestLinks:
    def test_absolute_links(self):
        html = '<html><body><a href="https://other.com/page">link</a></body></html>'
        resp = make_response(html)
        assert 'https://other.com/page' in resp.links

    def test_relative_links_qualified(self):
        html = '<html><body><a href="/about">about</a></body></html>'
        resp = make_response(html)
        assert 'https://example.com/about' in resp.links

    def test_no_links(self):
        html = '<html><body><p>No links</p></body></html>'
        resp = make_response(html)
        assert resp.links == ()

    def test_links_cached(self):
        html = '<html><body><a href="/a">a</a></body></html>'
        resp = make_response(html)
        first = resp.links
        second = resp.links
        assert first is second

    def test_links_deduplicate(self):
        html = '<html><body><a href="/a">A</a><a href="/a">A again</a></body></html>'
        resp = make_response(html)
        assert resp.links == ('https://example.com/a',)

    def test_relative_bare_path(self):
        html = '<html><body><a href="page.html">link</a></body></html>'
        resp = make_response(html)
        assert resp.links == ('https://example.com/page.html',)

    def test_relative_protocol_relative(self):
        html = '<html><body><a href="//other.com/page">link</a></body></html>'
        resp = make_response(html)
        assert resp.links == ('https://other.com/page',)


# ── Images ──────────────────────────────────────────────────────────────


class TestImages:
    def test_extracts_images(self):
        html = '<html><body><img src="https://example.com/logo.png"></body></html>'
        resp = make_response(html)
        assert 'https://example.com/logo.png' in resp.images

    def test_relative_images_qualified(self):
        html = '<html><body><img src="/img/logo.png"></body></html>'
        resp = make_response(html)
        assert 'https://example.com/img/logo.png' in resp.images

    def test_no_images(self):
        html = '<html><body><p>No images</p></body></html>'
        resp = make_response(html)
        assert resp.images == ()

    def test_images_deduplicate(self):
        html = '<html><body><img src="/img.png"><img src="/img.png"></body></html>'
        resp = make_response(html)
        assert resp.images == ('https://example.com/img.png',)

    def test_images_mixed_absolute_relative(self):
        html = '<html><body><img src="/img.png"><img src="https://example.com/logo.png"></body></html>'
        resp = make_response(html)
        assert len(resp.images) == 2
        assert 'https://example.com/img.png' in resp.images
        assert 'https://example.com/logo.png' in resp.images


# ── Tree ─────────────────────────────────────────────────────────────────


class TestTree:
    def test_tree_returns_html_element(self):
        resp = make_response('<html><body><p>Hello</p></body></html>')
        tree = resp.tree()
        from lxml.html import HtmlElement

        assert isinstance(tree, HtmlElement)

    def test_tree_parses_content(self):
        resp = make_response('<html><body><p id="x">Hi</p></body></html>')
        assert resp.tree().xpath('//p[@id="x"]/text()') == ['Hi']

    def test_tree_cached(self):
        resp = make_response('<html></html>')
        assert resp.tree() is resp.tree()

    def test_tree_empty_html_raises_error(self):
        resp = make_response('')
        from lxml.etree import ParserError

        with pytest.raises(ParserError):
            resp.tree()


# ── Soup ─────────────────────────────────────────────────────────────────


class TestSoup:
    def test_soup_returns_beautifulsoup(self):
        pytest.importorskip('bs4')
        resp = make_response('<html><body><p>Hello</p></body></html>')
        soup = resp.soup()
        from bs4 import BeautifulSoup

        assert isinstance(soup, BeautifulSoup)

    def test_soup_parses_content(self):
        pytest.importorskip('bs4')
        resp = make_response('<html><body><p id="x">Hi</p></body></html>')
        assert resp.soup().find('p', id='x').text == 'Hi'

    def test_soup_custom_parser(self):
        pytest.importorskip('bs4')
        resp = make_response('<html><body><p>Test</p></body></html>')
        soup = resp.soup(parser='lxml')
        assert soup.find('p').text == 'Test'


# ── Markdown ─────────────────────────────────────────────────────────────


class TestMarkdown:
    def test_markdown_converts_html(self):
        pytest.importorskip('html2text')
        resp = make_response('<html><body><p><strong>Hello</strong></p></body></html>')
        md = resp.markdown()
        assert 'Hello' in md

    def test_markdown_with_xpath(self):
        pytest.importorskip('html2text')
        resp = make_response('<html><body><div id="content"><p>Only this</p></div><p>Not this</p></body></html>')
        md = resp.markdown(content_xpath='//div[@id="content"]')
        assert 'Only this' in md
        assert 'Not this' not in md

    def test_markdown_xpath_no_match(self):
        pytest.importorskip('html2text')
        resp = make_response('<html><body><p>Hi</p></body></html>')
        assert resp.markdown(content_xpath='//nonexistent') == ''

    def test_markdown_ignore_links_true(self):
        pytest.importorskip('html2text')
        resp = make_response('<html><body><a href="https://example.com">click</a></body></html>')
        md = resp.markdown(ignore_links=True)
        assert 'click' in md
        assert '](' not in md

    def test_markdown_ignore_links_false(self):
        pytest.importorskip('html2text')
        resp = make_response('<html><body><a href="https://example.com">click</a></body></html>')
        md = resp.markdown(ignore_links=False)
        assert 'click' in md
        assert 'https://example.com' in md


# ── XPath ────────────────────────────────────────────────────────────────


class TestXpath:
    def test_xpath_finds_elements(self):
        resp = make_response('<html><body><p>One</p><p>Two</p></body></html>')
        assert len(resp.xpath('//p')) == 2

    def test_xpath_text_content(self):
        resp = make_response('<html><body><p>Hello</p></body></html>')
        assert resp.xpath('//p/text()') == ['Hello']

    def test_xpath_attribute(self):
        resp = make_response('<html><body><a href="/page">link</a></body></html>')
        assert resp.xpath('//a/@href') == ['/page']

    def test_xpath_no_match(self):
        resp = make_response('<html></html>')
        assert resp.xpath('//nonexistent') == []


# ── Iterlinks ────────────────────────────────────────────────────────────


class TestIterlinks:
    def test_iterlinks_finds_all_links(self):
        resp = make_response('<html><body><a href="/a">A</a><img src="/img.png"></body></html>')
        links = list(resp.iterlinks())
        assert len(links) == 2

    def test_iterlinks_empty(self):
        resp = make_response('<html><body><p>No links</p></body></html>')
        assert list(resp.iterlinks()) == []


# ── Itertext ─────────────────────────────────────────────────────────────


class TestItertext:
    def test_itertext_finds_text(self):
        resp = make_response('<html><body><p>Hello</p><p>World</p></body></html>')
        texts = list(resp.itertext())
        assert 'Hello' in texts
        assert 'World' in texts

    def test_itertext_empty(self):
        resp = make_response('<html><body><div></div></body></html>')
        assert list(resp.itertext()) == []


# ── TextContent ──────────────────────────────────────────────────────────


class TestTextContent:
    def test_text_content_returns_text(self):
        resp = make_response('<html><body><p>Hello <strong>World</strong></p></body></html>')
        text = resp.text_content()
        assert 'Hello' in text
        assert 'World' in text

    def test_text_content_empty(self):
        resp = make_response('<html><body></body></html>')
        assert resp.text_content() == ''


# ── Getattr delegation ───────────────────────────────────────────────────


class TestGetattr:
    def test_delegates_status_code(self):
        resp = make_response('<html></html>')
        assert resp.status_code == 200

    def test_delegates_text(self):
        resp = make_response('<p>Hello</p>')
        assert resp.text == '<p>Hello</p>'

    def test_delegates_url(self):
        resp = make_response('<html></html>', url='https://custom.com')
        assert resp.url == 'https://custom.com'

    def test_delegates_content_bytes(self):
        resp = make_response('<p>test</p>')
        assert resp.content == b'<p>test</p>'

    def test_missing_attribute_raises_error(self):
        resp = make_response('<html></html>')
        with pytest.raises(AttributeError):
            _ = resp.nonexistent_attr


# ── Error Handling (missing parsers) ─────────────────────────────────


class TestErrorHandling:
    def test_tree_raises_import_error_without_lxml(self):
        resp = make_response('<html></html>')
        with patch.dict('sys.modules', {'lxml': None}):
            with pytest.raises(ImportError, match='Lxml is not installed'):
                resp.tree()

    def test_soup_raises_import_error_without_bs4(self):
        resp = make_response('<html></html>')
        with patch.dict('sys.modules', {'bs4': None}):
            with pytest.raises(ImportError, match='BeautifulSoup is required for HTML parsing'):
                resp.soup()

    def test_markdown_raises_import_error_without_html2text(self):
        pytest.importorskip('lxml')
        resp = make_response('<html></html>')
        with patch.dict('sys.modules', {'html2text': None}):
            with pytest.raises(ImportError, match='Html2text is required for markdown extraction'):
                resp.markdown()


# ── Non-HTML Responses ───────────────────────────────────────────────


class TestNonHtmlResponses:
    def test_json_body_links_empty(self):
        pytest.importorskip('lxml')
        resp = make_response('{"key": "value"}')
        assert resp.links == ()

    def test_json_body_images_empty(self):
        pytest.importorskip('lxml')
        resp = make_response('{"key": "value"}')
        assert resp.images == ()

    def test_json_body_tables_empty(self):
        pytest.importorskip('lxml')
        resp = make_response('{"key": "value"}')
        assert resp.tables == []

    def test_plain_text_links_empty(self):
        pytest.importorskip('lxml')
        resp = make_response('Just some plain text with no HTML tags')
        assert resp.links == ()

    def test_json_body_emails_extracted(self):
        resp = make_response('{"email": "user@example.com"}')
        assert 'user@example.com' in resp.emails

    def test_plain_text_phone_numbers_extracted(self):
        resp = make_response('Call (555) 123-4567 for info')
        assert '(555) 123-4567' in resp.phone_numbers


# ── Repr ────────────────────────────────────────────────────────────────


class TestRepr:
    def test_repr(self):
        resp = make_response('<html></html>')
        assert 'Status: 200' in repr(resp)
        assert 'Elapsed Time' in repr(resp)
