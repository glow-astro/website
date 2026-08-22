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

Then the data-integrity half. Each of these was added after the corresponding
bug shipped, so none of them is hypothetical:

```python
import yaml, os, collections
topics = yaml.safe_load(open('_data/topics.yml'))
wps    = yaml.safe_load(open('_data/work_packages.yml'))
pubs   = yaml.safe_load(open('_data/publications.yml'))
tasks  = {t['code'] for w in wps for t in w['tasks']}
arxiv  = {p['arxiv'] for p in pubs['papers']}

cells, rows = collections.Counter(), collections.Counter()
for t in topics:
    for k in ('id','title','short','row','column','tint','card','blurb','wps','papers'):
        if k not in t: print('TOPIC MISSING FIELD', t.get('id'), k)
    cells[(t['row'], t['column'])] += 1
    rows[t['row']] += 1
    if not os.path.exists(f"{t['id']}.html"): print('TOPIC WITHOUT PAGE', t['id'])
    for c in t['wps']:
        if c not in tasks: print('TOPIC WPS UNKNOWN TASK', t['id'], c)
    for a in t['papers']:
        if a not in arxiv: print('TOPIC PAPER UNKNOWN', t['id'], a)
    # media is OPTIONAL; `media.file` overrides the stem, and `media.static`
    # means a plot (one .png) rather than an animation (webm + mp4 + poster)
    if 'media' in t:
        stem = t['media'].get('file', t['id'])
        for suffix in (('.png',) if t['media'].get('static') else ('.webm', '.mp4', '_still.png')):
            if not os.path.exists(f"media/{stem}{suffix}"):
                print('MISSING MEDIA', t['id'], stem + suffix)
for cell, n in cells.items():
    if n > 1: print('CELL COLLISION', cell, n)   # two cards stacked in the diagram
for r, n in rows.items():
    if n != 3: print('ROW NOT 3', r, n)          # a hole in the absolute grid
```

And the citations, whose failure mode is silent — `cite.html` renders nothing
for a key that is not in the page's `refs:`, so a typo removes a marker rather
than producing a broken one. Numbering is per page: `references.yml` is a
shared pool, and a page's own `refs:` front matter fixes both which entries it
cites and what number each gets.

```python
import re, io, glob, os, yaml
pool = {r['id'] for r in yaml.safe_load(open('_data/references.yml'))}
for src in sorted(glob.glob('*.html')):
    txt  = io.open(src, encoding='utf-8').read()
    fm   = re.match(r"---\n(.*?)\n---\n", txt, re.S)
    refs = (yaml.safe_load(fm.group(1)) or {}).get('refs') if fm else None
    cited = []
    for m in re.finditer(r'cite\.html key="([^"]+)"', txt):
        for k in (x.strip() for x in m.group(1).split(',')):
            if k not in cited: cited.append(k)
    if not cited and not refs: continue
    for k in cited:
        if   k not in pool:            print('KEY NOT IN BIBLIOGRAPHY', src, k)
        elif k not in (refs or []):    print('CITED BUT NOT IN refs:', src, k)
    for k in (refs or []):
        if   k not in pool:            print('refs ENTRY UNKNOWN', src, k)
        elif k not in cited:           print('IN refs BUT NEVER CITED', src, k)
    h = io.open(os.path.join('_site', src), encoding='utf-8').read()
    for key, n in re.findall(r'<a href="#ref-([a-z0-9-]+)">(\d+)</a>', h):
        if key not in (refs or []) or refs.index(key) + 1 != int(n):
            print('NUMBER WRONG', src, key, n)
    if '<sup class="cite">[]</sup>' in h: print('EMPTY MARKER', src)
    anchors = set(re.findall(r'<li id="ref-([a-z0-9-]+)"', h))
    miss = {k for k, _ in re.findall(r'<a href="#ref-([a-z0-9-]+)">(\d+)</a>', h)} - anchors
    if miss: print('MARKER WITHOUT LIST ENTRY', src, miss)
```

An entry in `refs:` that is never cited is not broken output, but on this site
it has always meant a citation was deleted and its entry left behind — and now
it also shifts every number after it, so it is checked.

Two more on the media, both of which have bitten:

```python
# nothing in media/ unreferenced, nothing referenced missing
refd = set()
for f in glob.glob('_site/*.html'):
    refd |= set(re.findall(r'"/media/([^"]+)"', io.open(f, encoding='utf-8').read()))
have = {os.path.basename(p) for p in glob.glob('media/*')}
if have - refd: print('ORPHANED MEDIA', sorted(have - refd))
if refd - have: print('MEDIA MISSING', sorted(refd - have))

# no page may play the same video twice
for f in glob.glob('_site/*.html'):
    v = re.findall(r'"/media/([^"]+)\.webm"', io.open(f, encoding='utf-8').read())
    dup = [x for x in set(v) if v.count(x) > 1]
    if dup: print('REPEATED VIDEO', os.path.basename(f), dup)
```

**Never reuse a media filename for different content.** Doing so serves every
returning visitor the old video out of cache, which presents as a page showing
the wrong animation — or the same one twice — while the file on disk is
correct, so it looks like a template bug and is not one. Give the new render a
new name and point `media.file` at it.

Also check every `src`/`poster`/`srcset` resolves under `_site`: a stale
`topic_id` once emptied a page's media paths to `/media/.webm`, and the page
still looked fine because the poster simply never appeared.

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
--bg: #0a0c11;  --bg-raised: #12151d;  --bg-card: #151926;  --border: #2a3040;
--text: #e8eaf0;  --text-soft: #c2c8d6;  --text-mute: #9198a8;
--accent: #f2a45c;  --accent-strong: #ffc389;  --accent-dim: #c07a34;
--accent-visited: #d3a37f;
--link-line: …/.45;  --accent-wash: …/.14;  --accent-halo: …/.50;  /* derived */
--cyan: #6fd8ee;          /* hover / focus */
--radius: 10px;  --measure: 1000px;
--font: system-ui, -apple-system, "Segoe UI", Roboto, ...
```

**The accent means "link" and nothing else.** Headings that borrowed it made
lists of names unreadable — the names and the band above them were the same
colour. Section headings are neutral; caps, letter-spacing and a trailing rule
carry the hierarchy instead.

Anything tinted with the accent — the underline under a link, the wash behind a
badge, the halo on the News pulse — gets a **token derived from `--accent`**,
never a hand-written `rgba()`. Three of them were still the pre-amber violet
long after the palette changed, because they were literals nobody thought to
grep for. Changing the project's colour is the four `--accent*` lines and
nothing else.

### Links

Two families, and a component belongs to exactly one:

| | looks like | who |
| --- | --- | --- |
| **In prose** | amber, 1px underline, → cyan on hover | anything inside a `<p>`, `<li>`, `<dd>`, caption |
| **Its own affordance** | no underline, usually not amber | `.site-nav`, `.subnav`, `.topicnav`, `.btn`, `.card-link`, `.skymap-card`, `.brand`, `.skip-link` |

- The underline is not decoration. It is what a reader who cannot separate amber
  from body text has to go on — colour is never the only signal (§7 above).
- A component in the second family sets `text-decoration: none` **in its own
  rule**, next to the padding and background that make it a button. There is no
  central opt-out list; a collected selector would put the declaration a hundred
  lines away from the thing it describes.
- `.card-title` is the hybrid: undecorated at rest, underlined on hover, because
  a title alone on its line reads as a heading until you reach for it.
- Link text names its destination. Never "here", "this link", "click". Trailing
  punctuation stays outside the link.
- External links are styled exactly like internal ones: no icon, no new tab,
  always `rel="noopener"`. The outbound links here are few and their text
  already says where they go ("CORDIS, grant agreement 101230608", "The GLoW
  code on GitHub"); an icon on each would speckle the prose for no gain.

### Emphasis

**Emphasis never carries colour**, because amber already means "link" — a
coloured word would look clickable. Weight and slope are all there is:

- `<strong>` — the one claim in a section that has to survive skimming.
- `<em>` — contrastive stress: the word that changes the sentence if you move
  it. *"the **range** of masses"*, *"**statistics**, not individual events"*.
- Never both on one span, never more than a clause, and never a whole sentence.
- Inside dimmed text (`.lede`, captions, `.roles` descriptions) both lift back
  to the body colour. That is a return to full brightness, not a new colour.
  Inside a link they inherit the amber instead, or a bolded link would go grey.

The budget is deliberate: across seventeen pages the site uses `<em>` twice and
`<strong>` four times in prose, plus the standing GLOW/GLoW note. That is the
level to hold. If a paragraph needs emphasis to be readable, the sentence is
usually the thing to fix.

**`<strong>` means emphasis and nothing else** — `grep '<strong>' _site/*.html`
should return only emphasis, and it does. A label in front of a value is not
emphasis: that is a `<dl class="roles">` with `<dt>`/`<dd>` (the twelve of them
were `<li><strong>…</strong><span>…</span></li>` until this rule arrived). A
card title inside a link is not emphasis either — see `.skymap-title`.

The canonical emphasis on this site is the naming note, where the contrast *is*
the sentence: **GLOW** is the project, **GLoW** is the code.

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
  controls. Honour it in any new animation. An animation that is a *sequence*
  rather than a loop goes through `_includes/figure-ondemand.html` instead:
  `controls`, no `autoplay`, no `loop`, and **the last frame as the poster**, so
  it plays once on request and settles back onto the picture it started from.
  That form needs no reduced-motion handling at all, because nothing moves until
  the reader asks. Choose by the animation: a loop that any frame represents, or
  a sweep that has an end.
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

---

## 11. The review host (GLOW)

The site is read by collaborators before it is read by anyone else. That needs
real authentication, not a hidden URL: a static site has already delivered its
prose, its figures and its unpublished claims to the browser by the time any
JavaScript password prompt could appear, and `curl` never sees the prompt at
all.

Two things it must **not** be:

- **GitHub Pages from a private repository.** The repository is private; the
  published site is not. Access control for Pages is a GitHub Enterprise Cloud
  feature. Making the source private and sharing the Pages link publishes the
  whole site.
- **An unguessable URL.** One forwarded mail, one link in a talk, one crawler
  following a referrer, and it is public. Fine for a screenshot, not for the
  project's unreleased science.

### How it works

**Cloudflare Pages** hosts the built site; **Cloudflare Access** stands in front
of it. A reader must be on an email allowlist and enter a one-time code before
Cloudflare serves a byte. Free: Pages hosting is free, Zero Trust is free to 50
users. Per-person, so no shared password circulates and someone can be removed
later.

It is a *preview* deployment, at `https://<branch>.<project>.pages.dev`, because
Cloudflare's one-click Access toggle covers previews on `pages.dev`; protecting a
production hostname means attaching a custom domain first. Nothing here needs a
domain, which is deliberate — `glow-erc.org` stays unspent while the naming
question is open (see the `glow-astro` discussion).

Deployment is **direct upload of the built site**. No remote, no CI, no source
leaves the machine — consistent with §9: the owner builds, reads, and decides.

```sh
tools/deploy_review.sh -n      # build and check, upload nothing
tools/deploy_review.sh         # ... and upload
```

### One-time setup

1. Create a Cloudflare account, then a Pages project. The first
   `tools/deploy_review.sh` offers to create it; or make it in the dashboard
   under **Workers & Pages → Create → Pages → Direct Upload**.
2. `*.pages.dev` is one global namespace, so the name may be taken. Whatever it
   ends up as, export it — the script derives the URL from it, and the build
   bakes that URL into every canonical link:

   ```sh
   export GLOW_PAGES_PROJECT=glow-erc-review
   ```
3. **Turn Access on.** Until this is done the deployment is public.
   *Settings → General → Access policy → Enable*, then *Zero Trust → Access →
   Applications →* the preview app, and add each collaborator's email to the
   policy.
4. Check it from a private window, signed out. If the page loads without asking
   for a code, Access is not on.

### What differs from a production build

Only two things, and only two on purpose: a review build that differs from what
will be published is a review of the wrong thing.

- `url:` points at the review host. Otherwise `_includes/head.html` would stamp
  every canonical link, the OpenGraph image and the JSON-LD with
  `https://glow-erc.org` — seeding the wrong canonical for a site that does not
  exist yet, and handing anyone who copies a link a dead address.
- `robots.txt` becomes `Disallow: /`, via `site.review`. Redundant behind Access,
  and kept for the window before the toggle is flipped.

`_config.review.yml` carries both. `tools/jekyll_build.rb` takes overlay config
files as extra arguments and honours `SITE_URL` from the environment; the review
address lives in neither file, because it is unknown until the Pages project
exists and would rot if hardcoded.

The build goes to `_review_site`, never `_site` — a build with a Disallow
robots.txt and the wrong canonical sitting in the production output directory is
how it eventually gets published.

### The checks

`deploy_review.sh` runs these before anything leaves the machine, and each has a
specific failure in mind:

- the production domain appears **nowhere** in the output — it appears in 17
  files of a normal build, so this fires loudly if `SITE_URL` fails to take;
- the review URL *does* appear in `index.html`, which catches a typo'd
  `SITE_URL` that the first check would pass by accident;
- `robots.txt` disallows crawling;
- no `glow-site-text*` or `*.odt` reached the build — `_config.yml` excludes
  them, but that file is the whole site's prose with tracked changes and open
  questions in it, so verify rather than trust.
