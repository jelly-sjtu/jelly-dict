"""HTML parsing helpers shared between English / Japanese parsers."""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

_WHITESPACE_RE = re.compile(r"\s+")


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", (text or "")).strip()


def text_or_empty(node: Tag | None) -> str:
    if node is None:
        return ""
    return normalize_text(node.get_text(" ", strip=True))


def absolute_url(base: str, href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(base, href)


def strip_furigana(node: Tag | NavigableString | None) -> str:
    """Return text content of a node with <ruby> furigana removed.

    <ruby>食<rt>た</rt>べる</ruby> -> '食べる'
    """
    if node is None:
        return ""
    if isinstance(node, NavigableString):
        return _join_cjk(normalize_text(str(node)))
    clone = BeautifulSoup(str(node), "lxml")
    for rt in clone.find_all("rt"):
        rt.decompose()
    for rp in clone.find_all("rp"):
        rp.decompose()
    return _join_cjk(normalize_text(clone.get_text(" ", strip=True)))


_CJK_SPACE_RE = re.compile(
    r"([぀-ゟ゠-ヿ一-鿿㐀-䶿])"
    r"\s+"
    r"([぀-ゟ゠-ヿ一-鿿㐀-䶿])"
)


def _join_cjk(text: str) -> str:
    """Collapse spaces that Naver inserts between adjacent CJK chars."""
    prev = None
    while prev != text:
        prev = text
        text = _CJK_SPACE_RE.sub(r"\1\2", text)
    return text


def ruby_html(node: Tag | NavigableString | None) -> str:
    """Return inner HTML preserving <ruby> tags (for Anki export)."""
    if node is None:
        return ""
    if isinstance(node, NavigableString):
        return str(node).strip()
    return "".join(str(child) for child in node.children).strip()


def first(soup: BeautifulSoup | Tag, selector: str) -> Tag | None:
    return soup.select_one(selector)


def all_(soup: BeautifulSoup | Tag, selector: str) -> list[Tag]:
    return list(soup.select(selector))


_NUMBER_RE = re.compile(r"\d+")


def extract_number(node: Tag | None) -> int:
    """Extract the first integer from a node's text. Returns 0 if missing."""
    if node is None:
        return 0
    text = node.get_text(" ", strip=True)
    match = _NUMBER_RE.search(text)
    return int(match.group()) if match else 0


def dedup_preserve_order(values) -> list[str]:
    """Return values with duplicates removed while preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def common_prefix_len(a: str, b: str) -> int:
    """Return the length of the longest common prefix between two strings."""
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n
