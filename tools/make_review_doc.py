#!/usr/bin/env python3
"""Flatten the built site into one document for prose review in OpenOffice.

    ruby tools/jekyll_build.rb . _site
    python3 tools/make_review_doc.py            # -> /tmp/glow-site-text.odt
    python3 tools/make_review_doc.py out.odt

Reads `_site`, not the sources, so what lands in the document is exactly what a
reader sees -- including everything rendered out of `_data`. Keeps headings,
paragraphs, lists and figure captions; drops navigation, images, video and the
footer repeated on every page.

Round-tripping is the point, so every page carries a SOURCE line naming the
files its text actually comes from. That matters more here than it looks: most
of this site's prose lives in `_data/*.yml` rather than in the page that shows
it, so "I changed this paragraph on the programme page" is not enough to find it
again. The data files are discovered by scanning each source page for
`site.data.<name>`, so the line cannot go stale as pages change.

Headings stay real headings, so Writer's Navigator gives an outline and
track-changes works normally. Hand the edited file back and the changes can be
applied to the sources.
"""
import io, os, re, subprocess, sys, glob
from bs4 import BeautifulSoup
import yaml

SITE = "_site"
DEFAULT_OUT = "/tmp/glow-site-text.odt"

# Reading order for a human, which is not the nav order: the case first, then
# the six topics it points at, then the plan, then the people and the outputs.
PAGES = [
    ("index.html",          "Home"),
    # The news archive. Its items are the same ones the home page shows, so
    # most of it is a second read of prose already above -- but the heading and
    # lede are its own, and the generator is right that a page nobody reviews
    # is a page nobody reviews.
    ("news.html",           "News archive"),
    ("science.html",        "Science — the case"),
    ("sources.html",        "Science — distant and strong-field sources"),
    ("dark-matter.html",    "Science — dark matter and small scales"),
    ("testing-gravity.html","Science — testing gravity and dark energy"),
    ("wave-optics.html",    "Science — wave optics"),
    ("microlensing.html",   "Science — microlensing"),
    ("data-analysis.html",  "Science — data analysis"),
    ("programme.html",      "Research programme"),
    ("team.html",           "Team"),
    ("publications.html",   "Publications and talks"),
    ("software.html",       "Software and data"),
    # Unlinked on the site (2026-09-02), so a reader will not stumble on it,
    # but it is prose the owner has to read before it goes anywhere. Listed
    # here for that reason and not because the site navigates to it.
    ("glow_code.html",      "Software — GLoW (unlinked draft)"),
    ("join.html",           "Join"),
    ("contact.html",        "Contact"),
    ("404.html",            "404"),
]

# Screen CSS is irrelevant here; this is what Writer will import as styles.
CSS = """
body { font: 11pt/1.45 'Liberation Serif', Georgia, serif; color: #000; }
h1 { font-size: 19pt; margin: 0 0 6pt; }
h2 { font-size: 15pt; margin: 20pt 0 5pt; }
h3 { font-size: 12.5pt; margin: 13pt 0 4pt; }
h4 { font-size: 11pt; margin: 11pt 0 3pt; font-style: italic; }
p, li { margin: 0 0 6pt; }
ul { margin: 0 0 8pt; padding-left: 18pt; }
.pagehead { font-size: 9pt; letter-spacing: .1em; text-transform: uppercase; color: #666; }
.source { font-size: 8.5pt; color: #777; font-family: 'Liberation Mono', monospace; }
.lede { font-style: italic; }
.cap { font-size: 9.5pt; color: #444; }
.meta { font-size: 9.5pt; color: #444; }
.url { font-size: 8pt; color: #888; font-family: 'Liberation Mono', monospace; }
.note { font-size: 10pt; color: #7a4a00; border-left: 3pt solid #d99; padding-left: 6pt; }
"""

NOTES_FILE = "_data/review_notes.yml"

DROP = ["header", "footer", ".skip-link", "script", "style", "noscript",
        "img", "video", "iframe", "picture", "source",
        ".topicnav", ".subnav", ".btn-row"]


def load_notes():
    """Open review questions, keyed by page -- see _data/review_notes.yml."""
    if not os.path.exists(NOTES_FILE):
        return {}
    return yaml.safe_load(io.open(NOTES_FILE, encoding="utf-8")) or {}


def data_sources(page):
    """Which _data files feed this page, read off the source template."""
    if not os.path.exists(page):
        return []
    src = io.open(page, encoding="utf-8").read()
    names = sorted(set(re.findall(r"site\.data\.(\w+)", src)))
    # The layout adds these to every page; naming them each time is noise.
    return [f"_data/{n}.yml" for n in names if n not in ("nav",)]


def lift_media_descriptions(soup):
    """Rescue alt / aria-label text before the media elements are dropped.

    These are full sentences describing every figure, they are what a screen
    reader actually reads out, and nobody proofreads them because they are
    invisible. Lifted into a paragraph beside the caption so they get read like
    everything else.
    """
    for fig in soup.find_all("figure"):
        for el in fig.find_all(["img", "video"]):
            desc = el.get("alt") or el.get("aria-label") or ""
            desc = " ".join(desc.split())
            if not desc:
                continue
            p = soup.new_tag("p")
            p["class"] = "cap"
            p.string = "[image description] " + desc
            cap = fig.find("figcaption")
            cap.insert_before(p) if cap else fig.append(p)


def flatten(path, title, notes=()):
    html = io.open(os.path.join(SITE, path), encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")
    lift_media_descriptions(soup)
    for sel in DROP:
        for el in soup.select(sel):
            el.decompose()
    main = soup.find("main") or soup.body

    origin = ", ".join([path] + data_sources(path))
    out = [f'<h2>{title}</h2>',
           f'<p class="source">SOURCE: {origin}</p>']

    # The diagram's cards are anchors holding <strong>/<span>, so the block-level
    # sweep below would miss them -- and they are `title`/`card` straight out of
    # topics.yml, which is exactly the kind of text this document exists to get
    # reviewed. Pull them out first, then remove them so nothing repeats.
    cards = main.select(".skymap-card")
    if cards:
        out.append('<h3>Diagram cards</h3>')
        for c in cards:
            # .skymap-title / .skymap-blurb, not <strong>/<span>: the card title
            # stopped being a <strong> when emphasis was given a convention, and
            # this silently emitted an empty label for a while.
            title = c.select_one(".skymap-title")
            blurb = c.select_one(".skymap-blurb")
            label = title.get_text(" ", strip=True) if title else ""
            body = blurb.get_text(" ", strip=True) if blurb else ""
            if not label:
                print(f"WARNING: {path}: a diagram card has no .skymap-title")
            out.append(f"<li><b>{label}</b> — {body}</li>")
        for c in cards:
            c.decompose()

    pending = list(notes)
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "figcaption",
                             "dt", "dd", "table"]):
        # Nested blocks are reached through their parent; do not emit twice.
        # `table` is in that list because its cells are prose too -- a row label
        # and four one-word cells are as much reviewable text as a paragraph is,
        # and before this they were silently absent from the document.
        if el.find_parent(["li", "figcaption", "table"]):
            continue
        text = " ".join(el.get_text(" ", strip=True).split())
        if not text:
            continue

        frag = el.decode_contents()
        # A link's target is invisible once this becomes a Writer document, and
        # the external ones are claims worth checking. Internal ones are not.
        if "<a " in frag:
            sub = BeautifulSoup(frag, "html.parser")
            for a in sub.find_all("a"):
                href = a.get("href", "")
                if href.startswith("http"):
                    a.insert_after(BeautifulSoup(f' <span class="url">&lt;{href}&gt;</span>',
                                                 "html.parser"))
            frag = str(sub)

        # Inline badges ("New" on a news item) are separated by CSS on screen
        # and by nothing at all once the styling is gone.
        frag = re.sub(r"</span>(?=\w)", "</span> ", frag)

        cls = set(el.get("class") or [])
        name = el.name
        if name == "table":
            # Flattened to one line per row rather than reproduced as a table.
            # What is under review here is the wording of the labels and the
            # caption, not the ruling; and an ODT table that the owner edits in
            # place would be far harder to read changes back out of than a list.
            cap = el.find("caption")
            if cap is not None:
                out.append('<p class="cap">[table] '
                           + cap.decode_contents() + '</p>')
            for tr in el.find_all("tr"):
                cells = [" ".join(c.get_text(" ", strip=True).split())
                         for c in tr.find_all(["th", "td"])]
                cells = [c for c in cells if c]
                if not cells:
                    continue
                out.append("<li><b>" + cells[0] + "</b> &mdash; "
                           + " &middot; ".join(cells[1:]) + "</li>"
                           if len(cells) > 1 else f"<li>{cells[0]}</li>")
        elif name == "figcaption":
            out.append(f'<p class="cap">[figure] {frag}</p>')
        elif name == "li":
            out.append(f"<li>{frag}</li>")
        elif name in ("dt", "dd"):
            out.append(f'<p class="meta">{frag}</p>')
        else:
            # Demote: page h1/h2/h3 sit under this document's h2 per page.
            level = {"h1": "h3", "h2": "h3", "h3": "h4", "h4": "h4"}.get(name, name)
            k = ""
            if "lede" in cls:
                k = ' class="lede"'
            elif cls & {"card-meta", "eyebrow", "card-title", "news-date", "authors", "journal"}:
                k = ' class="meta"'
            out.append(f"<{level}{k}>{frag}</{level}>")

        # An open question belongs beside the paragraph it is about, so it is
        # emitted as soon as that paragraph goes past.
        for note in [n for n in pending if n.get("after", "") in text]:
            out.append(f'<p class="note">NOTE: {note["text"].strip()}</p>')
            pending.remove(note)

    # A stale anchor must not swallow the note. Say which one, and keep it.
    for note in pending:
        print(f"WARNING: {path}: no paragraph matches "
              f"{note.get('after', '')!r} -- note moved to the end of the page")
        out.append(f'<p class="note">NOTE (unplaced): {note["text"].strip()}</p>')

    body = "\n".join(out)
    return re.sub(r"(?:<li>.*?</li>\s*)+", lambda m: "<ul>" + m.group(0) + "</ul>",
                  body, flags=re.S)


def main():
    missing = [p for p, _ in PAGES if not os.path.exists(os.path.join(SITE, p))]
    if missing:
        sys.exit(f"not built: {missing} -- run ruby tools/jekyll_build.rb . _site")

    # Anything built but not listed would be reviewed by nobody. Say so rather
    # than silently shipping a partial document.
    built = {os.path.basename(f) for f in glob.glob(f"{SITE}/*.html")}
    unlisted = sorted(built - {p for p, _ in PAGES})
    if unlisted:
        print("WARNING: built but not in this document:", ", ".join(unlisted))

    parts = [f"<style>{CSS}</style>",
             "<h1>GLOW &mdash; full site text</h1>",
             '<p class="meta">Every word the site shows, in reading order, for '
             'editing in OpenOffice. Navigation, images and video are omitted; '
             'external link targets are shown in angle brackets. Each page '
             'names the files its text comes from &mdash; most of it lives in '
             '<span class="url">_data/*.yml</span>, not in the page.</p>',
             '<p class="meta">Track changes is the easiest way to hand this '
             'back (Edit &rarr; Track Changes &rarr; Record).</p>']
    notes = load_notes()
    stale = sorted(set(notes) - {p for p, _ in PAGES})
    if stale:
        print("WARNING: review_notes.yml names pages that are not in this "
              "document:", ", ".join(stale))
    parts += [flatten(p, t, notes.get(p, [])) for p, t in PAGES]

    # The EU statement is identical in every footer, so it was dropped above.
    # It is also obligatory wording, so it gets reviewed once, here.
    foot = BeautifulSoup(io.open(f"{SITE}/index.html", encoding="utf-8").read(),
                         "html.parser").find("footer")
    if foot:
        parts.append('<h2>Footer (every page)</h2>'
                     '<p class="source">SOURCE: _config.yml (eu:), _includes/footer.html</p>'
                     f'<p>{" ".join(foot.get_text(" ", strip=True).split())}</p>')

    tmp = "/tmp/glow-site-text.html"
    io.open(tmp, "w", encoding="utf-8").write("\n".join(parts))

    dest = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
    outdir, base = os.path.dirname(dest), os.path.basename(dest)
    subprocess.run(["soffice", "--headless", "--convert-to", "odt",
                    "--outdir", outdir, tmp],
                   check=True, capture_output=True)
    produced = os.path.join(outdir, "glow-site-text.odt")
    if produced != dest:
        os.replace(produced, dest)
    print(dest, os.path.getsize(dest), "bytes")


if __name__ == "__main__":
    main()
