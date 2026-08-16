# How this site is built

Written to be handed to a fresh session starting a **different** site — the GLOW
project site — so it does not have to rediscover any of this. Copy it into the
new repository (as `CLAUDE.md`, or keep it as `docs/SITE_CONVENTIONS.md` and
point at it), or reference this absolute path:

    /home/mzuma/code/miguelzuma.github.io/docs/SITE_CONVENTIONS.md

Everything below describes `miguelzuma.github.io`, the personal academic site.
The last section covers what changes for GLOW.

---

## 1. Stack

Plain **Jekyll**, no theme, no gem beyond `jekyll-sitemap`. GitHub Pages builds
from `master`. There is no CSS framework, no build step for assets, and no
JavaScript framework: one hand-written stylesheet and three small scripts.

That choice is deliberate. An academic site is read for its content, changes a
few times a year, and must still build in five years. Every dependency is a
future breakage.

```
_config.yml            site metadata, author, both affiliations
_data/*.yml            all repeated content (see §4)
_layouts/default.html  <html>, header, footer, script tags
_layouts/page.html     default + eyebrow / h1 / lede block, for interior pages
_includes/             head, header, footer, subnav, and the CV renderers
assets/css/main.css    the whole stylesheet, ~1100 lines, sectioned by comment
assets/js/             three scripts, described in §6
*.html                 one file per page, front matter + markup
cv.tex                 LaTeX CV generated from the same data as cv.html (§5)
tools/                 build scripts (§3)
imgs/, files/          images and downloadable PDFs
```

Pages are `.html`, not `.md`: the content is structured (cards, lists with
links and badges) rather than prose, and Liquid in HTML is clearer than
Markdown fighting inline tags.

## 2. Local preview

```sh
ruby tools/jekyll_build.rb . _site        # "Built 12 pages -> _site"
cd _site && python3 -m http.server 8794 --bind 127.0.0.1
```

`tools/jekyll_build.rb` exists because RubyGems' dependency activation broke on
this machine; it loads Jekyll from `~/.local/share/gem` directly. Use it rather
than `bundle exec jekyll`.

Bind to `0.0.0.0` instead of `127.0.0.1` to read the site on a phone on the same
Wi-Fi (find the address with `ip -4 addr show scope global`). That exposes the
draft to the local network, so stop the server afterwards.

**CSS and JS cache hard. Always hard-reload (`ctrl+shift+r`) before believing
what the browser shows.**

## 3. Verification, every time

After any structural change, rebuild and run this. It has caught duplicate ids
and dead anchors repeatedly:

```python
import re, glob, os
ids, anchors = {}, []
for f in glob.glob('_site/*.html'):
    h = open(f, encoding='utf-8').read()
    seen = {}
    for m in re.finditer(r'\sid="([^"]+)"', h):
        seen[m.group(1)] = seen.get(m.group(1), 0) + 1
    dups = [k for k, v in seen.items() if v > 1]
    if dups: print('DUPLICATE ids', os.path.basename(f), dups)
    ids[os.path.basename(f)] = set(seen)
    for m in re.finditer(r'href="([^"]*#[^"]+)"', h):
        anchors.append((os.path.basename(f), m.group(1)))
for src, href in anchors:
    if href.startswith('http'): continue
    page, frag = href.split('#', 1)
    t = os.path.basename(page) if page else src
    if t in ids and frag not in ids[t]: print('BROKEN', src, '->', href)
```

For a refactor that should not change what a reader sees, extract the visible
words from `<main>` before and after and diff them. A word-for-word match is
proof; reading the template is not.

Check the result in a real browser. The Chrome tooling works well, but note
that a **hidden or unfocused tab does not run `requestAnimationFrame`**, so
smooth scrolling silently does nothing and scroll-driven JavaScript never
fires. Use `behavior: 'instant'` when scripting scroll, and dispatch a `resize`
event to force a synchronous re-run of scroll-spy logic.

## 4. Content lives in `_data`, never in the templates

The single most important pattern here. Anything that repeats — people,
projects, software, news, CV entries, navigation — is a YAML list rendered by a
loop. Adding a group member is a five-line YAML edit, not an HTML edit.

Each data file opens with a comment documenting its schema, including which
fields are optional and what the template does with each. Keep that up when
adding a field.

- `nav.yml` — site navigation; each `id` matches a page's `nav:` front-matter
  key, which is how the active link is marked.
- `people.yml` — `current`, `visitors`, `alumni`, `earlier_mentees`. Each person
  has a `stage` (`postdoc|phd|masters|intern|undergrad`) that both groups the
  cards and labels the alumni rows.
- `projects.yml` — `current` projects and past `positions`. Optional
  `funding_logo: {src, alt}` renders a funder acknowledgment.
- `news.yml` — dated one-sentence items; see §7.
- `cv.yml` — every CV section, shared by the HTML page and the PDF.
- `tex.yml` — literal strings that cannot be written inline in Liquid, because
  Liquid ends a `{{ ... }}` at the first `}` even inside a quoted string.

Front matter carries only what is unique to a page: `title`, `eyebrow`, `lede`,
`description`, `nav`, and `sections` for the in-page bar.

## 5. One source, two outputs (the CV)

`_data/cv.yml` renders to **both** `cv.html` and `cv.tex`, and `people.yml`
supplies the supervision section of the PDF. `tools/build_cv.sh` builds the
site, then runs `pdflatex` twice over `_site/cv.tex`, writing
`files/CV_Miguel_Zumalacarregui.pdf`. That PDF is committed, because GitHub
Pages cannot run LaTeX.

`cv.tex` carries `layout: null` and `sitemap: false` so Jekyll renders it as a
page without wrapping it in HTML.

Escaping LaTeX from Liquid has three traps, all solved in
`_includes/tex-escape.html` — read it before touching it:

1. Liquid terminates `{{ ... }}` at the first `}`, even inside quotes, so
   brace literals live in `_data/tex.yml`.
2. Liquid's `replace` runs on Ruby's `gsub`, where `\&` in the replacement
   means "the whole match" — escaping `&` needs `'\\&'`.
3. Liquid discards output that is only whitespace, so a space cannot be emitted
   from inside a tag; a newline left in the template survives and LaTeX reads
   it as a space.

If you build the same thing for GLOW (a PDF and a page from one source), copy
these three includes wholesale rather than rediscovering the traps.

## 6. JavaScript: three scripts, each doing one thing

Everything degrades: with JavaScript off, the site is fully readable.

- `subnav.js` — the sticky in-page section bar. Measures the header height
  rather than hard-coding it, and marks the section in view with
  `aria-current`. At the foot of the page it marks the last section, because a
  short final section never reaches the cutoff.
- `anchor-aliases.js` — redirects the old site's dead fragments
  (`research.html#pbh` → `#main-program`) so external links keep working.
- `external-links.js` — gives off-site links and the site's own PDFs
  `target="_blank"` and `rel="noopener"`. One rule beats two hundred attributes
  scattered across pages and data files.

## 7. Design

Dark, quiet, typographic. No decoration that is not carrying information.

```css
--bg: #0a0c11;  --bg-card: #151926;  --border: #2a3040;
--text: #e8eaf0;  --text-soft: #c2c8d6;  --text-mute: #9198a8;
--accent: #b7a2ff;  --accent-strong: #d0c2ff;  --accent-dim: #8b74e8;
--cyan: #6fd8ee;          /* hover / focus */
--radius: 10px;  --measure: 1000px;
--font: system-ui, -apple-system, "Segoe UI", Roboto, ...
```

**The accent means "link" and nothing else.** Headings that borrowed it made
lists of names unreadable — the names and the band above them were the same
colour. Section headings are neutral; caps, letter-spacing and a trailing rule
carry the hierarchy instead.

Other rules worth keeping:

- System font stack, no web fonts. Nothing to load, nothing to go missing.
- One measure (`--measure: 1000px`) for text, so line length stays readable.
- Cards for anything list-like; a floated logo inside a card needs
  `.card::after { clear: both }` or it bleeds into the next card.
- Two floated images in one card must be `float: right; clear: right`, and the
  second must come *after* the first in the source — a float cannot rise above
  its position in flow.
- Match stacked logos on **width**, not height, when their aspect ratios differ.
- A `prefers-reduced-motion` block pauses autoplaying video and exposes
  controls. Honour it in any new animation.
- There is a print stylesheet. Check any new page prints sensibly.

Accessibility is not optional: real `alt` text on anything informative and
`alt=""` on decoration, focus outlines left visible, `aria-current` on the
active nav item, colour never the only signal (the active nav link gets an
underline bar as well as a colour).

The **News** list on the home page is worth copying. Items are dated in
`news.yml`; a "New" flag is derived by comparing each item's date against a
90-day window from `site.time`, so it expires by itself at the next build
rather than being hand-placed and going stale.

## 8. Voice and style

These came from the site's owner. They matter more than the code.

- **US spelling** throughout: program, catalog, analyze, center, modeling,
  toward. Published paper titles keep their own spelling, as do institution
  names and the `aria-labelledby` attribute.
- **First person.** "My research", "I work on" — not "Zumalacárregui's research".
- **Never the possessive for people.** "The group", "the students" — never "my
  group", "my postdoc".
- **No bragging.** No citation counts, h-index, headcounts, rankings or view
  counts. Application documents do that; a website does not. If a sentence
  exists to impress rather than to inform, cut it.
- **Say what a thing is, not how good it is.** "Accurate at the sub-percent
  level, meeting the requirements of current surveys" survives; "getting this
  right is unglamorous and essential" reads as salesmanship.
- **Claims must be defensible.** Do not promise multi-messenger detections that
  are unlikely; do not state a lower bound that propagates a misconception.
- **Describe relationships precisely.** In `people.yml`, roles follow one shape,
  `Role, Institution (relationship)`, where the relationship is one of
  `(co-supervised)`, `(co-supervised with X)`, `(close collaboration)`. The last
  is for people never formally supervised — say what the connection *was*, not
  what it was not. Group people by what they did, never by whether they
  finished.
- **GLOW** in all caps is the ERC project. **GLoW**, lowercase "o", is the
  software. They are different things and the distinction is load-bearing.

## 9. Working practice

- Commit in small, coherent steps with a real subject line and a body saying
  *why*. The git log is documentation.
- **Do not push without being asked.** The owner reads all prose before
  publishing.
- Comments explain the non-obvious — why a float needs `clear`, why a Liquid
  workaround exists — not what the next line does.
- When the owner supplies edited text, apply it as written, fix only outright
  typos, and raise disagreements separately rather than quietly overriding.
- Text review runs through an ODT: extract the visible prose from `_site`,
  convert with `soffice --convert-to 'odt:writer8'`, and diff the returned file
  against the current build. Include figure captions — they are text a reader
  sees. If LibreOffice is already open, the converter needs
  `-env:UserInstallation=file:///tmp/lo-profile` or it silently does nothing.

---

## 10. What differs for the GLOW site

Reuse the stack, the build tooling, the data-driven pattern, the verification
routine, and §8 wholesale. Differences to plan for:

**It is a project site, not a personal one.** The voice shifts from "I" to
"we"/"the project". §8's ban on the possessive still holds.

**EU funding obligations are real requirements, not decoration.** A
Horizon-Europe-funded site must display the EU emblem with the words "Funded by
the European Union", and normally a disclaimer that views expressed are the
author's and do not necessarily reflect those of the European Union or the
granting authority. Grant agreement **101230608**; CORDIS record at
<https://cordis.europa.eu/project/id/101230608>. The dark-background emblem
already prepared for this site is `imgs/erc_eu_funding_dark.png` — note that
the official "dark" file has a navy "Funded by the European Union" wordmark
that is illegible on a dark background, and was recoloured to the white variant
the emblem rules provide. Source files are in
`~/Dropbox/Documentos/GLOW_ERC_project/Logos/`.

**Content it will need that this site does not have:** work packages (WP1–WP3,
listed in `_data/projects.yml`), team profiles with project assignments, open
positions, deliverables and publications, and outreach. The personal site's
GLOW card says a dedicated project site "is in preparation" — update or remove
that line once the new site is live, and cross-link the two.

**Likely reusable files, more or less unchanged:** `_layouts/`, `_includes/`
(head, header, footer, subnav), `assets/css/main.css`, all three scripts,
`tools/jekyll_build.rb`, and the `_data` schema comments. A distinct accent
colour would be reasonable — the GLOW logo is warm orange against this site's
violet — but change it as a token in one place, and keep the rule that the
accent means "link".
