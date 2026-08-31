#!/usr/bin/env uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4",
#     "html2text",
# ]
# ///

"""Re-extract the Canvas Help Center into the canvas-platform skill's two files.

The Help Center (Pylon-hosted, https://help.canvasmedical.com) documents Canvas's
*native platform features*. It has no local build and serves no clean markdown
(`llms-full.txt` 404s; appending `.md` returns the article HTML unchanged), so the
only source is the article HTML, fetched over the network.

Writes the two files the `canvas-platform` skill bundles, into this repo's
`canvas-plugin-assistant/skills/canvas-platform/` directory:

  - canvas_platform_context.txt : the full-body corpus. One `----- BEGIN PAGE
    <url>` / `----- END PAGE <url>` entry per article, sorted by URL, in the same
    delimiter format as the canvas-sdk corpus so the skill's read/cite workflow
    works unchanged.
  - canvas_platform_index.txt : a compact discovery index. The Help Center's own
    category headings from llms.txt, a `- [Title](url)` bullet per article, and
    each article's <h2>/<h3> subsection outline as an indented sub-list.

An agent greps the small index for keywords, reads the one matching article's
body from the corpus by its URL, and cites that URL.
"""

import re
import sys
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import html2text
from bs4 import BeautifulSoup, Tag

HELP_BASE_URL = "https://help.canvasmedical.com"
LLMS_INDEX_URL = f"{HELP_BASE_URL}/llms.txt"

# Pylon renders the article body server-side into this container (the class list
# carries `kb-article-body--ssr`), so the full prose and its <h1>/<h2>/<h3>
# headings are in the initial HTML -- no JS execution needed.
ARTICLE_CONTAINER_CLASS = "kb-article-body"

# The canvas-platform skill's directory holds SKILL.md alongside the two files it
# bundles; resolve it relative to this script (…/scripts/ -> …/skills/…).
SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "canvas-platform"
CONTEXT_FILE = SKILL_DIR / "canvas_platform_context.txt"
INDEX_FILE = SKILL_DIR / "canvas_platform_index.txt"

# Alert type -> label for markdown conversion.
ALERT_LABELS = {
    "alert__info": "Info",
    "alert__warning": "Warning",
    "alert__danger": "Danger",
}

# llms.txt structure: `##`/`###`/`####` category headings and
# `- [Title](https://help.canvasmedical.com/articles/<id>-<slug>)` bullets.
HEADING_RE = re.compile(r"^(?P<hashes>#{2,4}) (?P<text>.+?)\s*$")
BULLET_RE = re.compile(
    r"^- \[(?P<title>.+?)\]"
    r"\((?P<url>https://help\.canvasmedical\.com/articles/[^)]+)\)\s*$"
)


def preprocess_code_blocks(soup: BeautifulSoup, container: Tag) -> None:
    """Convert Rouge-highlighted code blocks to markdown fenced blocks."""
    for div in container.find_all("div", class_="highlighter-rouge"):
        classes = div.get("class", [])
        lang = ""
        for cls in classes:
            if cls.startswith("language-"):
                lang = cls.removeprefix("language-")
                break

        code_tag = div.find("code")
        if not code_tag:
            continue

        code_text = code_tag.get_text()
        # Strip single trailing newline that Rouge adds.
        if code_text.endswith("\n"):
            code_text = code_text[:-1]

        replacement = soup.new_tag("pre")
        replacement.string = f"```{lang}\n{code_text}\n```"
        div.replace_with(replacement)


def preprocess_alerts(soup: BeautifulSoup, container: Tag) -> None:
    """Convert alert aside elements to blockquote-style markdown."""
    for aside in container.find_all("aside", class_="alert"):
        classes = aside.get("class", [])
        label = "Note"
        for cls in classes:
            if cls in ALERT_LABELS:
                label = ALERT_LABELS[cls]
                break

        content_div = aside.find("div", class_="alert__content")
        if not content_div:
            continue

        # Get inner HTML so html2text can process links etc.
        inner_html = content_div.decode_contents()
        replacement = soup.new_tag("blockquote")
        replacement.append(
            BeautifulSoup(f"<p><strong>{label}:</strong> {inner_html}</p>", "html.parser")
        )
        aside.replace_with(replacement)


def preprocess_tabs(soup: BeautifulSoup, container: Tag) -> None:
    """Add tab labels before each tab content panel."""
    for tab_menu in container.find_all("ul", class_="tab"):
        tab_id = tab_menu.get("data-tab")
        if not tab_id:
            continue

        # Collect tab names.
        tab_names = []
        for li in tab_menu.find_all("li", recursive=False):
            a = li.find("a")
            if a:
                tab_names.append(a.get_text(strip=True))

        # Find corresponding tab-content.
        content_ul = container.find("ul", class_="tab-content", id=tab_id)
        if not content_ul:
            continue

        # Add a heading before each tab panel's content.
        content_items = content_ul.find_all("li", recursive=False)
        for i, li in enumerate(content_items):
            name = tab_names[i] if i < len(tab_names) else f"Tab {i + 1}"
            label = soup.new_tag("p")
            label.string = f"**{name}**"
            li.insert(0, label)

        # Remove the tab menu (the labels are now inline).
        tab_menu.decompose()


def extract_content_from_html(html: str, container_class: str = ARTICLE_CONTAINER_CLASS) -> str | None:
    """Extract and convert article content from a raw HTML string.

    Returns None when the container is absent, which is the signal that Pylon
    changed its markup: the caller skips the article rather than emitting blank.
    """
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find("div", class_=container_class)
    if not container:
        return None

    # Remove unwanted elements.
    for tag_name in ("header", "script", "style", "svg", "nav", "footer"):
        for el in container.find_all(tag_name):
            el.decompose()

    # Remove anchor links (the # links after headings).
    for a in container.find_all("a", class_="article__anchor"):
        a.decompose()

    # Pre-process special elements before html2text.
    preprocess_code_blocks(soup, container)
    preprocess_alerts(soup, container)
    preprocess_tabs(soup, container)

    # Convert HTML to markdown.
    h = html2text.HTML2Text()
    h.body_width = 0
    h.unicode_snob = False
    h.protect_links = False
    h.wrap_links = False
    h.mark_code = False
    h.ul_item_mark = "-"

    md = h.handle(str(container))

    # Replace smart quotes with plain ASCII equivalents.
    md = md.translate(str.maketrans("‘’“”", "''\"\""))

    # Strip blank lines to produce dense markdown.
    dense = "\n".join(line for line in md.splitlines() if line.strip())

    return dense


def extract_outline(
    html: str,
    container_class: str = ARTICLE_CONTAINER_CLASS,
    levels: tuple[str, ...] = ("h2", "h3"),
) -> list[tuple[int, str]]:
    """Return the (level, text) subsection outline of an article body.

    Collects the given heading levels in document order. The article's top-level
    <h1> is never collected (it duplicates the page title). Used to build the
    grep-able discovery index alongside the full-body corpus.
    """
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", class_=container_class)
    if not container:
        return []

    outline: list[tuple[int, str]] = []
    for heading in container.find_all(list(levels)):
        text = heading.get_text(strip=True)
        if text:
            outline.append((int(heading.name[1]), text))
    return outline


@dataclass
class IndexNode:
    """One line of llms.txt worth keeping: a category heading or an article bullet."""

    kind: str  # "heading" | "article"
    raw: str  # the verbatim source line (headings/bullets are re-emitted as-is)
    url: str = ""  # article nodes only


def fetch(url: str) -> str:
    """Fetch a URL and return its decoded body (the default network fetcher)."""
    req = urllib.request.Request(url, headers={"User-Agent": "canvas-docs-context-generator"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (https only)
        return resp.read().decode("utf-8")


def parse_llms_index(text: str) -> list[IndexNode]:
    """Parse llms.txt into ordered category-heading and article-bullet nodes."""
    nodes: list[IndexNode] = []
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            nodes.append(IndexNode(kind="heading", raw=f"{heading['hashes']} {heading['text']}"))
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            nodes.append(IndexNode(kind="article", raw=line.rstrip(), url=bullet["url"]))
    return nodes


def write_context_entry(f, url: str, content: str) -> None:
    """Append one corpus entry, byte-for-byte matching the canvas-sdk corpus format."""
    f.write(f"----- BEGIN PAGE {url}\n")
    f.write(content)
    f.write(f"\n----- END PAGE {url}\n\n\n")


def write_index(
    path: Path,
    nodes: list[IndexNode],
    included: set[str],
    outlines: dict[str, list[tuple[int, str]]],
) -> None:
    """Write the discovery index: llms.txt headings + surviving bullets + outlines."""
    lines: list[str] = []
    for node in nodes:
        if node.kind == "heading":
            if lines:
                lines.append("")
            lines.append(node.raw)
        elif node.url in included:
            lines.append(node.raw)
            for level, text in outlines.get(node.url, []):
                lines.append(f"{'    ' * (level - 1)}- {text}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@dataclass
class BuildStats:
    articles: int = 0  # distinct article URLs in llms.txt
    included: int = 0  # articles with a non-empty body (written to both files)
    empty: list[str] = field(default_factory=list)  # skipped (empty body / fetch miss)


def build(
    context_path: Path = CONTEXT_FILE,
    index_path: Path = INDEX_FILE,
    fetch_url: Callable[[str], str] = fetch,
    index_url: str = LLMS_INDEX_URL,
    container_class: str = ARTICLE_CONTAINER_CLASS,
) -> BuildStats:
    """Scrape the Help Center and write the corpus + index.

    An article appears in *both* outputs iff its body is non-empty; the two files
    therefore stay in sync (every index URL resolves to a corpus BEGIN PAGE
    block). A body that comes back empty is the signal that Pylon changed its
    markup, so it is logged and skipped rather than emitted blank.

    Bodies (the large data) are streamed to the corpus and flushed per article so
    a late crash keeps its progress; only the small per-article outlines are held
    in memory to assemble the index at the end.
    """
    nodes = parse_llms_index(fetch_url(index_url))
    urls = sorted({n.url for n in nodes if n.kind == "article"})

    outlines: dict[str, list[tuple[int, str]]] = {}
    included: set[str] = set()
    stats = BuildStats(articles=len(urls))

    with open(context_path, "w", encoding="utf-8") as cf:
        for i, url in enumerate(urls, 1):
            html = fetch_url(url)
            body = extract_content_from_html(html, container_class)
            if not body:
                print(f"  WARN: empty body, skipping {url}", file=sys.stderr)
                stats.empty.append(url)
                continue
            write_context_entry(cf, url, body)
            cf.flush()
            outlines[url] = extract_outline(html, container_class)
            included.add(url)
            print(f"  [{i}/{len(urls)}] {url}")

    write_index(index_path, nodes, included, outlines)
    stats.included = len(included)
    return stats


def main() -> None:
    stats = build()
    print(
        f"Wrote {stats.included}/{stats.articles} articles to "
        f"{CONTEXT_FILE.name} + {INDEX_FILE.name}"
    )
    if stats.empty:
        print(f"Skipped {len(stats.empty)} empty-body article(s):", file=sys.stderr)
        for url in stats.empty:
            print(f"  - {url}", file=sys.stderr)


if __name__ == "__main__":
    main()
