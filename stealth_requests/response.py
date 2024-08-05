from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml.html import HtmlElement
    from bs4 import BeautifulSoup


def tree(self) -> HtmlElement:
    from lxml import html
    return html.fromstring(self.content)

def soup(self, parser: str = 'html.parser') -> BeautifulSoup:
    from bs4 import BeautifulSoup
    return BeautifulSoup(self.content, parser)

