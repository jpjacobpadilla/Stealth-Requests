from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml.html import HtmlElement
    from bs4 import BeautifulSoup


@dataclass
class Metadata:
    title: str | None
    description: str | None
    thumbnail: str | None
    author: str | None
    keywords: tuple[str] | None
    twitter_handle: str | None
    robots: tuple[str] | None
    canonical: str | None

PARSER_IMPORT_SOLUTION = "Install it using 'pip install stealth-requests[parsers]'."


class StealthResponse():
    def __init__(self, resp):
        self._response = resp

        self._tree: HtmlElement | None = None
        self._important_meta_tags: Metadata | None = None
        self._links: tuple[str] = tuple()
        self._images: tuple[str] = tuple()

    def __getattr__(self, name):
        return getattr(self._response, name)

    def _get_tree(self) -> HtmlElement:
        try:
            from lxml import html
        except ImportError:
            raise ImportError(f'Lxml is not installed. {PARSER_IMPORT_SOLUTION}')

        self._tree = html.fromstring(self.content)
        return self._tree

    def tree(self) -> HtmlElement:
        if self._tree is not None:
            return self._tree
        return self._get_tree()

    def soup(self, parser: str = 'html.parser') -> BeautifulSoup:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(f'BeautifulSoup is required for markdown extraction. {PARSER_IMPORT_SOLUTION}')

        return BeautifulSoup(self.content, parser)

    def markdown(self, content_xpath: str | None = None, ignore_links: bool = True):
        from lxml import etree
        try:
            import html2text
        except ImportError:
            raise ImportError(f'Html2text is required for markdown extraction. {PARSER_IMPORT_SOLUTION}')

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = ignore_links

        tree = self.tree()
        if content_xpath:
            tree = tree.xpath(content_xpath)[0]
        html = etree.tostring(tree, pretty_print=True, method="html").decode()

        return text_maker.handle(html)

    def xpath(self, xp: str):
        return self.tree().xpath(xp)

    def iterlinks(self, *args, **kwargs):
        return self.tree().iterlinks(*args, **kwargs)

    def itertext(self, *args, **kwargs):
        return self.tree().itertext(*args, **kwargs)

    def text_content(self, *args, **kwargs):
        return self.tree().text_content(*args, **kwargs)

    @staticmethod
    def _format_meta_list(content: str) -> tuple[str]:
        items = content.split(',')
        return tuple(item.strip() for item in items)

    def _set_important_meta_tags(self) -> Metadata:
        tree = self.tree()

        title = tree.xpath('//head/title/text()')
        description = tree.xpath('//head/meta[@name="description"]/@content')
        thumbnail = tree.xpath('//head/meta[@property="og:image"]/@content')
        author = tree.xpath('//head/meta[@name="author"]/@content')
        keywords = tree.xpath('//head/meta[@name="keywords"]/@content')
        twitter_handle = tree.xpath('//head/meta[@name="twitter:site"]/@content')
        robots = tree.xpath('//head/meta[@name="robots"]/@content')
        canonical = tree.xpath('//head/link[@rel="canonical"]/@href')

        self._important_meta_tags = Metadata(
            title = title[0] if title else None,
            description = description[0] if description else None,
            thumbnail = thumbnail[0] if thumbnail else None,
            author = author[0] if author else None,
            keywords = self._format_meta_list(keywords[0]) if keywords else None,
            twitter_handle = twitter_handle[0] if twitter_handle else None,
            robots =  self._format_meta_list(robots[0]) if robots else None,
            canonical = canonical[0] if canonical else None
        )
        return self._important_meta_tags

    @property
    def meta(self):
        return self._important_meta_tags or self._set_important_meta_tags()

    def _parse_links(self, tag: str) -> tuple[str]:
        formatted_links = []

        parsed_url = urlparse(self._response.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for element, _, link, _ in self.tree().iterlinks():
            if element.tag == tag:
                if link.startswith('/'):
                    formatted_links.append(base_url + link)
                else:
                    formatted_links.append(link)

        return tuple(formatted_links)

    @property
    def images(self):
        if not self._images:
            self._images = self._parse_links('img')
        return self._images

    @property
    def links(self):
        if not self._links:
            self._links = self._parse_links('a')
        return self._links

    def __repr__(self):
        return f'<StealthResponse [Status: {self._response.status_code} Elapsed Time: {self._response.elapsed:.2f} seconds]>'