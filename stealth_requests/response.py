from __future__ import annotations

from dataclasses import dataclass
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

        self._tree = None 
        self._important_meta_tags = None
    
    def __getattr__(self, name):
        return getattr(self._response, name)

    def _get_tree(self):
        try:
            from lxml import html
        except ImportError:
            raise ImportError(f'Lxml is not installed. {PARSER_IMPORT_SOLUTION}')

        self._tree = html.fromstring(self.content)
        return self._tree

    def tree(self) -> HtmlElement:
        return self._tree or self._get_tree()    

    def soup(self, parser: str = 'html.parser') -> BeautifulSoup:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(f'BeautifulSoup is required for markdown extraction. {PARSER_IMPORT_SOLUTION}')

        return BeautifulSoup(self.content, parser)
    
    def markdown(self):
        try:
            import html2text
        except ImportError:
            raise ImportError(f'Html2text is required for markdown extraction. {PARSER_IMPORT_SOLUTION}')

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        return text_maker.handle(str(self.soup()))
    
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
        canonical = tree.xpath('//head/link[@rel="canonical"]/@content')

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
