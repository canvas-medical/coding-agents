"""Tests for generate_platform_context module (the Help Center scraper).

Runs offline against small stubbed fixtures via an injected fetcher.
"""

import re
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from conftest import MockContextManager

import generate_platform_context as gen

# =============================================================================
# Fixtures: a stub llms.txt index + a handful of stub article HTML pages
# =============================================================================

U1 = "https://help.canvasmedical.com/articles/1001-managing-appointments"
U2 = "https://help.canvasmedical.com/articles/1002-canvas-chat"
U3 = "https://help.canvasmedical.com/articles/1003-processing-payments"
U4 = "https://help.canvasmedical.com/articles/1004-broken"  # empty body -> dropped

STUB_LLMS = f"""# Canvas Medical Help Center


## Getting Started


### Onboarding & Setup

- [Managing Patient Appointments]({U1})
- [Canvas Chat and Bot]({U2})

## Revenue & Billing

- [Processing Payments]({U3})
- [Broken Article]({U4})
"""

# Article with a title <h1> (dropped from the index outline) plus nested
# <h2>/<h3> subsections and a curly apostrophe (must be ASCII-normalized).
PAGE_1001 = """<html><body>
<div class="kb-article-body kb-article-body--ssr">
<h1>Managing Patient Appointments</h1>
<p>Manage a patient’s visits in Canvas.</p>
<h2>Scheduling Appointments</h2>
<p>How to schedule an appointment.</p>
<h3>Recurring Appointments</h3>
<p>Set up recurring visits.</p>
<h2>Rescheduling &amp; Cancelling</h2>
<p>Move or cancel a booking.</p>
<h2>Appointment Reminders</h2>
<p>Canvas sends a single org-wide reminder.</p>
</div>
</body></html>"""

# Non-empty body with no subsections: keeps its index bullet, gets no sub-list.
PAGE_1002 = """<html><body>
<div class="kb-article-body kb-article-body--ssr">
<h1>Canvas Chat and Bot</h1>
<p>Chat helps staff communicate.</p>
</div>
</body></html>"""

PAGE_1003 = """<html><body>
<div class="kb-article-body kb-article-body--ssr">
<h1>Processing Payments</h1>
<p>Take payments in Canvas.</p>
<h2>Payment Methods</h2>
<p>Cards and saved methods.</p>
<h2>Refunds</h2>
<p>Issue a refund.</p>
</div>
</body></html>"""

# No kb-article-body container -> extract returns None -> skipped from both files.
PAGE_1004 = """<html><body>
<div class="some-other-class"><h1>Broken</h1></div>
</body></html>"""

PAGES = {U1: PAGE_1001, U2: PAGE_1002, U3: PAGE_1003, U4: PAGE_1004}


def _fake_fetch(url: str) -> str:
    if url == gen.LLMS_INDEX_URL:
        return STUB_LLMS
    return PAGES[url]


def _corpus_block(corpus: str, url: str) -> str:
    """Return the body between this URL's BEGIN/END markers."""
    begin = f"----- BEGIN PAGE {url}\n"
    end = f"----- END PAGE {url}"
    start = corpus.index(begin) + len(begin)
    return corpus[start : corpus.index(end, start)]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("platform")
    context_path = out / "canvas_platform_context.txt"
    index_path = out / "canvas_platform_index.txt"
    stats = gen.build(
        context_path=context_path,
        index_path=index_path,
        fetch_url=_fake_fetch,
    )
    return {
        "stats": stats,
        "context": context_path.read_text(encoding="utf-8"),
        "index": index_path.read_text(encoding="utf-8"),
    }


# =============================================================================
# build() — end-to-end corpus + index
# =============================================================================


class TestBuild:
    """Tests for the build orchestration and the two files it produces."""

    def test_format_begin_end_pairs_sorted_and_ascii(self, built):
        corpus = built["context"]
        begins = re.findall(r"^----- BEGIN PAGE (\S+)$", corpus, re.M)
        ends = re.findall(r"^----- END PAGE (\S+)$", corpus, re.M)
        assert begins == ends  # matched pairs, in the same order
        assert begins == sorted(begins)  # entries sorted by URL
        assert begins == [U1, U2, U3]  # empty-body article excluded
        for url in begins:
            assert _corpus_block(corpus, url).strip()  # bodies non-empty
        assert "’" not in corpus and "“" not in corpus  # ASCII-normalized

    def test_heading_hierarchy_preserved(self, built):
        block = _corpus_block(built["context"], U1)
        i_h1 = block.index("# Managing Patient Appointments")
        i_h2 = block.index("## Scheduling Appointments")
        i_h3 = block.index("### Recurring Appointments")
        assert i_h1 < i_h2 < i_h3  # nested #/##/### in document order

    def test_index_structure(self, built):
        index = built["index"]
        # Help Center category headings preserved
        assert "## Getting Started" in index
        assert "### Onboarding & Setup" in index
        assert "## Revenue & Billing" in index
        # one verbatim bullet per non-empty article
        assert f"- [Managing Patient Appointments]({U1})" in index
        assert f"- [Canvas Chat and Bot]({U2})" in index
        assert f"- [Processing Payments]({U3})" in index
        # subsections as an indented sub-list (h2 -> 4 spaces, h3 -> 8 spaces)
        assert "\n    - Scheduling Appointments\n" in index
        assert "\n        - Recurring Appointments\n" in index
        assert "\n    - Rescheduling & Cancelling\n" in index
        # the duplicated <h1> is dropped from the outline
        assert "    - Managing Patient Appointments" not in index
        # a subsection-less article keeps its bullet with no sub-list under it
        lines = index.splitlines()
        chat_idx = lines.index(f"- [Canvas Chat and Bot]({U2})")
        assert not lines[chat_idx + 1].startswith("    ")

    def test_two_tier_round_trip(self, built):
        index_lines = built["index"].splitlines()
        # 1. grep the index for a keyword -> land on a subsection line
        sub_idx = next(
            i
            for i, ln in enumerate(index_lines)
            if ln.startswith("    ") and "scheduling" in ln.lower()
        )
        # 2. its parent bullet carries the article URL to read
        url = next(
            gen.BULLET_RE.match(index_lines[j])["url"]
            for j in range(sub_idx, -1, -1)
            if gen.BULLET_RE.match(index_lines[j])
        )
        assert url == U1
        # 3. read that one article's body from the corpus and find the subsection
        assert "## Scheduling Appointments" in _corpus_block(built["context"], url)

    def test_non_empty_and_index_corpus_in_sync(self, built):
        corpus, index = built["context"], built["index"]
        assert corpus.strip() and index.strip()  # both non-empty
        corpus_urls = set(re.findall(r"^----- BEGIN PAGE (\S+)$", corpus, re.M))
        index_urls = {
            gen.BULLET_RE.match(ln)["url"]
            for ln in index.splitlines()
            if gen.BULLET_RE.match(ln)
        }
        assert corpus_urls == index_urls  # every index URL resolves to a corpus block
        assert corpus.count("----- BEGIN PAGE ") == built["stats"].included
        # the empty-body article is dropped from both, keeping the two files in sync
        assert U4 not in corpus_urls
        assert U4 not in index

    def test_stats_counts(self, built):
        stats = built["stats"]
        assert stats.articles == 4  # all four llms.txt bullets
        assert stats.included == 3  # only non-empty bodies
        assert stats.empty == [U4]  # the container-less article


# =============================================================================
# parse_llms_index()
# =============================================================================


class TestParseLlmsIndex:
    """Tests for parsing llms.txt into heading/article nodes."""

    def test_keeps_headings_and_article_bullets_in_order(self):
        nodes = gen.parse_llms_index(STUB_LLMS)
        kinds = [(n.kind, n.raw) for n in nodes]
        assert kinds[0] == ("heading", "## Getting Started")
        assert kinds[1] == ("heading", "### Onboarding & Setup")
        assert nodes[2].kind == "article"
        assert nodes[2].url == U1

    def test_drops_lines_that_are_neither_heading_nor_bullet(self):
        text = "plain prose line\n> a quote\n- [x](https://example.com/not-help)\n"
        assert gen.parse_llms_index(text) == []


# =============================================================================
# extract_content_from_html()
# =============================================================================


class TestExtractContentFromHtml:
    """Tests for the HTML -> dense-markdown article extractor."""

    def test_missing_container_returns_none(self):
        assert gen.extract_content_from_html(PAGE_1004) is None

    def test_strips_chrome_and_anchor_links(self):
        html = """<div class="kb-article-body">
        <header>nav header</header>
        <script>doss()</script>
        <style>.x{}</style>
        <svg><path/></svg>
        <nav>menu</nav>
        <footer>foot</footer>
        <h1>Title</h1>
        <a class="article__anchor" href="#s">#</a>
        <p>Real body text.</p>
        </div>"""
        md = gen.extract_content_from_html(html)
        assert "Real body text." in md
        for noise in ("nav header", "doss()", "menu", "foot", ".x{}"):
            assert noise not in md


class TestPreprocessCodeBlocks:
    """Tests for Rouge -> fenced-code-block conversion."""

    def _run(self, inner):
        soup = BeautifulSoup(f'<div class="c">{inner}</div>', "html.parser")
        container = soup.find("div", class_="c")
        gen.preprocess_code_blocks(soup, container)
        return container

    def test_language_class_and_trailing_newline_stripped(self):
        container = self._run(
            '<div class="highlighter-rouge language-python">'
            "<code>print(1)\n</code></div>"
        )
        assert container.find("pre").string == "```python\nprint(1)\n```"

    def test_no_language_class_yields_bare_fence(self):
        container = self._run('<div class="highlighter-rouge"><code>x=1</code></div>')
        assert container.find("pre").string == "```\nx=1\n```"

    def test_div_without_code_tag_is_skipped(self):
        container = self._run('<div class="highlighter-rouge language-py"></div>')
        assert container.find("pre") is None  # left untouched


class TestPreprocessAlerts:
    """Tests for alert-aside -> blockquote conversion."""

    def _run(self, inner):
        soup = BeautifulSoup(f'<div class="c">{inner}</div>', "html.parser")
        container = soup.find("div", class_="c")
        gen.preprocess_alerts(soup, container)
        return container

    def test_known_label_applied(self):
        container = self._run(
            '<aside class="alert alert__warning">'
            '<div class="alert__content">be careful</div></aside>'
        )
        bq = container.find("blockquote")
        assert "Warning:" in bq.get_text()
        assert "be careful" in bq.get_text()

    def test_unknown_class_defaults_to_note(self):
        container = self._run(
            '<aside class="alert"><div class="alert__content">heads up</div></aside>'
        )
        assert "Note:" in container.find("blockquote").get_text()

    def test_aside_without_content_div_is_skipped(self):
        container = self._run('<aside class="alert alert__info"></aside>')
        assert container.find("blockquote") is None


class TestPreprocessTabs:
    """Tests for tab-menu -> inline-label conversion."""

    def _run(self, inner):
        soup = BeautifulSoup(f'<div class="c">{inner}</div>', "html.parser")
        container = soup.find("div", class_="c")
        gen.preprocess_tabs(soup, container)
        return container

    def test_labels_inserted_and_menu_removed(self):
        container = self._run(
            '<ul class="tab" data-tab="t1"><li><a>First</a></li>'
            "<li><a>Second</a></li></ul>"
            '<ul class="tab-content" id="t1"><li>one</li><li>two</li></ul>'
        )
        labels = [p.string for p in container.find_all("p")]
        assert labels == ["**First**", "**Second**"]
        assert container.find("ul", class_="tab") is None  # menu decomposed

    def test_more_panels_than_names_falls_back_to_tab_n(self):
        # The second menu <li> has no <a>, so it contributes no tab name; the
        # second content panel then falls back to the "Tab N" label.
        container = self._run(
            '<ul class="tab" data-tab="t1"><li><a>Only</a></li><li></li></ul>'
            '<ul class="tab-content" id="t1"><li>one</li><li>two</li></ul>'
        )
        labels = [p.string for p in container.find_all("p")]
        assert labels == ["**Only**", "**Tab 2**"]

    def test_menu_without_data_tab_is_skipped(self):
        container = self._run('<ul class="tab"><li><a>x</a></li></ul>')
        assert container.find("ul", class_="tab") is not None  # untouched

    def test_menu_without_matching_content_is_skipped(self):
        container = self._run('<ul class="tab" data-tab="missing"><li><a>x</a></li></ul>')
        assert container.find("ul", class_="tab") is not None  # untouched


# =============================================================================
# extract_outline()
# =============================================================================


class TestExtractOutline:
    """Tests for the <h2>/<h3> subsection outline."""

    def test_missing_container_returns_empty(self):
        assert gen.extract_outline(PAGE_1004) == []

    def test_collects_levels_and_skips_h1_and_blank_headings(self):
        outline = gen.extract_outline(PAGE_1001)
        assert (1, "Managing Patient Appointments") not in outline  # h1 excluded
        assert outline[0] == (2, "Scheduling Appointments")
        assert (3, "Recurring Appointments") in outline

    def test_blank_heading_text_dropped(self):
        html = '<div class="kb-article-body"><h2>  </h2><h2>Kept</h2></div>'
        assert gen.extract_outline(html) == [(2, "Kept")]


# =============================================================================
# write_index()
# =============================================================================


class TestWriteIndex:
    """Tests for index assembly edge cases."""

    def test_leading_heading_gets_no_blank_line(self, tmp_path):
        nodes = [
            gen.IndexNode(kind="heading", raw="## First"),
            gen.IndexNode(kind="heading", raw="## Second"),
        ]
        path = tmp_path / "idx.txt"
        gen.write_index(path, nodes, included=set(), outlines={})
        # blank line inserted before the second heading, not the first
        assert path.read_text(encoding="utf-8") == "## First\n\n## Second\n"

    def test_excluded_article_bullet_omitted(self, tmp_path):
        nodes = [gen.IndexNode(kind="article", raw=f"- [x]({U1})", url=U1)]
        path = tmp_path / "idx.txt"
        gen.write_index(path, nodes, included=set(), outlines={})  # U1 not included
        assert path.read_text(encoding="utf-8") == "\n"


# =============================================================================
# fetch() — the real network path, mocked at urlopen
# =============================================================================


class TestFetch:
    """Tests for the default urllib fetcher."""

    def test_decodes_response_body(self):
        response = MockContextManager(read_data=b"<html>hi</html>")
        with patch.object(gen.urllib.request, "urlopen", return_value=response):
            assert gen.fetch("https://help.canvasmedical.com/llms.txt") == "<html>hi</html>"


# =============================================================================
# main()
# =============================================================================


class TestMain:
    """Tests for the CLI entry point."""

    def test_reports_totals_without_skips(self, capsys):
        stats = gen.BuildStats(articles=3, included=3, empty=[])
        with patch.object(gen, "build", return_value=stats):
            gen.main()
        out = capsys.readouterr()
        assert "Wrote 3/3 articles" in out.out
        assert "Skipped" not in out.err

    def test_reports_skipped_empty_bodies(self, capsys):
        stats = gen.BuildStats(articles=2, included=1, empty=[U4])
        with patch.object(gen, "build", return_value=stats):
            gen.main()
        err = capsys.readouterr().err
        assert "Skipped 1 empty-body article(s):" in err
        assert U4 in err
