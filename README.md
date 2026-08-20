# GLOW project site

Website for **GLOW — Gravitational Lensing of Waves**, an ERC Consolidator Grant
project (grant agreement 101230608).

Plain Jekyll, no theme, one hand-written stylesheet, two small scripts. The
conventions this site is built to — stack, data-driven content, verification
routine, design tokens and voice — are in
[`docs/SITE_CONVENTIONS.md`](docs/SITE_CONVENTIONS.md). Read that before making
structural changes.

## Local preview

```sh
tools/preview.sh                  # build, serve on :8811, open a browser
tools/preview.sh science.html     # open that page instead of the home page
tools/preview.sh -w               # rebuild whenever a source file changes
tools/preview.sh -h               # all the options
```

Stop it with ctrl-C. It builds into a scratch directory and swaps that in, so a
failed build leaves the previous `_site` in place rather than half-replaced —
you are never reading a stale page while believing it is the new one.

Its server sends `Cache-Control: no-store`, which is the point of using it over
a bare `python3 -m http.server`: **CSS, JS and images cache hard, and that has
produced two false bug reports here** — a sticky bar that looked missing when it
was only unstyled, and a figure that kept reporting its pre-edit height. With
this server you do not need `ctrl+shift+r`.

Underneath, it runs:

```sh
ruby tools/jekyll_build.rb . _site
```

`tools/jekyll_build.rb` loads Jekyll from `~/.local/share/gem` directly, working
around a RubyGems dependency-activation problem on this machine. Use it rather
than `bundle exec jekyll`.

After any structural change, rebuild and run the verification pass in
[`docs/SITE_CONVENTIONS.md`](docs/SITE_CONVENTIONS.md) §3. It has caught a
stale `topic_id` that silently emptied a page's media paths, and a page that
declared `sections` but never included the bar to render them.

## Prose review

```sh
ruby tools/jekyll_build.rb . _site
python3 tools/make_review_doc.py          # -> /tmp/glow-site-text.odt
python3 tools/make_review_doc.py glow-site-text.odt   # ... or somewhere you will find it
```

Flattens the built site into one `.odt` for reading and editing in
OpenOffice/LibreOffice — every word the site shows, in reading order, with
navigation, images and video stripped and external link targets spelled out.
Track changes (Edit → Track Changes → Record) is the easiest way to hand edits
back.

It reads `_site` rather than the sources, so nothing rendered out of `_data` can
go missing, and each page carries a `SOURCE:` line naming the files its text
actually comes from — necessary because **most of this site's prose lives in
`_data/*.yml`, not in the page that displays it**, and an edit is otherwise hard
to trace back. Those file lists are discovered by scanning each template for
`site.data.<name>`, so they cannot go stale.

`PAGES` in the script fixes the reading order; the script warns about any built
page missing from it rather than shipping a partial document.

## Deployment

The site is written to be served from the root of its domain (`baseurl` is
empty). On GitHub Pages that means an **organisation page repository**: create an
organisation, add a repository named `<org>.github.io`, push this tree to
`master`, and enable Pages on that branch. No `baseurl` change is needed.

If a custom domain is added later, put the hostname in a `CNAME` file at the
repository root and update `url:` in `_config.yml`.

## Editing content

Everything that repeats lives in `_data`, not in the templates:

| File | Contents |
| --- | --- |
| `nav.yml` | site navigation; each `id` matches a page's `nav:` front matter |
| `topics.yml` | the science topics: the diagram, the topic bar, and each topic page's header |
| `work_packages.yml` | WP1–WP3 and their lettered tasks |
| `people.yml` | PI, team members, external collaborators |
| `positions.yml` | **open calls only** — never what the project plans to recruit |
| `publications.yml` | papers and talks that acknowledge the grant |
| `references.yml` | works cited on the science page; **order is the numbering** |
| `news.yml` | dated one-sentence items for the home page |
| `software.yml` | tools, per-paper data releases, and the release policy |

### Science and work packages

Two pages describe the same research from different angles, and the division is
load-bearing:

- a **topic page** explains the physics — what a phenomenon is and what it can
  measure. Durable, broad audience.
- the **work-packages page** is the plan — what this grant builds, in what
  order, who leads it. Specialist audience, expires with the grant.

They cross-link in both directions, and both directions are derived from
`topics.yml`'s `wps` field, so they cannot disagree. Cross-link; do not repeat.

The topic **bar** is flat on purpose. An earlier version grouped it under
headings, which was wrong: microlensing is a wave-optics problem, a search
problem and a dark-matter probe at once, so any partition into kinds misleads.

### Citations

`science.html` and all six topic pages carry numbered citations, drawn from the
grant proposal's own bibliography so they support the same claims they supported
there. Cite with

```liquid
{% include cite.html key="planck-lensing" %}
{% include cite.html key="dsa2000,chord,burstt" %}
```

and the list renders itself at `#references` from `_includes/references.html`.

**`references.yml` is a pool, not a numbering.** Each page declares the entries
it cites, in first-appearance order, in its own `refs:` front matter, and *that*
is the numbering — so every page counts from 1 with no gaps, the same work is
`[3]` on one page and `[1]` on another, and trimming a page's citations
renumbers nothing but that page. Both the marker and the list read the page's
`refs:`, so they cannot disagree. Adding to `references.yml` is free; deleting
from it breaks every page that cites the entry, which the verification pass
catches.

Keep topic-page lists short — two or three. The science case is the place for
the full argument.

A key matching no entry renders an empty marker rather than failing the build,
so the verification pass checks it. Verify any new `url` resolves before
committing it; the ones here were all checked, and titles came from the arXiv
API rather than from memory.

### The science diagram

`science.html` leads with the source–lens–observer figure, above the section
bar, built by `_includes/skymap.html` from the same `topics.yml`. It is the one place
the topics are grouped, and that is not a contradiction with the flat bar:

- the **top row** is the light path. A card's column lines up with the
  source, the lens or the observer in the picture beneath it, so its position is
  **where the phenomenon acts** — a location, not a category. Microlensing and
  dark matter can both sit at the lens, which is the overlap a heading would
  have had to deny.
- the **bottom row** is what the project builds to measure any of it. It comes
  second because top-left is the strongest position on a figure and the science
  questions belong there.

The topic bar and the previous/next buttons follow the **file order**, which is
not the diagram order: the bar builds from wave optics, because the other five
lean on it. `row`/`column` place the cards, so the two orders differ freely.

Each topic therefore carries `row`, `column`, `tint` and a short `card` blurb.
The rows are absolutely positioned, so **no two topics may claim the same
(row, column)** and each row needs exactly three — a collision silently stacks
two cards on a busy image. The verification pass checks both.

`imgs/source_lens_observer.{jpg,webp}` is a frame from the GLOW outreach video.
The personal site carries the same image with its own card set; they are
independent copies on purpose.

Below 940px the cards drop out of the picture and stack beneath it, which loses
the positional argument — the figcaption states it in words for that case, and
for anyone reading without the image.

### Figures and animations

`media/` holds both: animations as `<stem>.webm` + `<stem>.mp4` + a poster, and
static plots as a single `.png`. They get the same frame on the page and the
same naming rule, and **`media` in `topics.yml` always means the page's opening
figure** — set `static: true` when that opener is a plot. Three topics open on
a figure that is not their own result, because the simple statement should come
before the project's version of it; the animation then follows in the section
that needs it. Static plots come from `~/code/application_plots/plots/`
— take the `_dark` variant, and downscale anything much wider than 2000px.

Animations live in `media/` as `<stem>.webm`, `<stem>.mp4` and
`<stem>_still.png`, where `<stem>` is `topics.yml`'s `media.file` or, failing
that, the topic id. Set `media.file` whenever the render is not specific to one
topic, so the filename says what the video shows.

**Never reuse a filename for different content.** Returning visitors get the old
video out of cache, which looks exactly like the page rendering the wrong
animation — or the same one twice — while the file on disk is right. This has
already cost one round of debugging. `media` is **optional** in `topics.yml` — `sources` has no
render, and `topic-figure.html` emits nothing rather than a broken `/media/.webm`
when the key is absent. They are **not** generated here — each comes from the repo
that owns the physics, indexed in `~/code/application_plots/ANIMATIONS.md`, and
each topic records which family it took in `topics.yml`'s `media.source`.

Take the `_web_dark` variant: this site is dark-only. Renders are not all the
same shape, so `media.width`/`media.height` carry each one's real pixel size —
they reserve the right space and stop the caption jumping on load. Read them off
the poster frame rather than assuming.

`assets/js/reduced-motion.js` pauses these for readers who ask for reduced
motion and exposes controls, so the setting hands the content over rather than
removing it.

Site-wide facts — grant number, host institution, the EU funding statement —
live in `_config.yml` so they cannot drift between pages.

## EU funding obligation

The emblem and the words "Funded by the European Union", together with the
disclaimer, appear in the footer of every page, driven by the `eu:` block in
`_config.yml`. Do not remove them, and do not alter the emblem image: the
supplied file is the white-wordmark variant the emblem rules require on a dark
background.
