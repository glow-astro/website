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
ruby tools/jekyll_build.rb . _site
cd _site && python3 -m http.server 8794 --bind 127.0.0.1
```

`tools/jekyll_build.rb` loads Jekyll from `~/.local/share/gem` directly, working
around a RubyGems dependency-activation problem on this machine. Use it rather
than `bundle exec jekyll`.

CSS and JS cache hard — hard-reload (`ctrl+shift+r`) before believing what the
browser shows. This has already caused one false bug report: a new sticky bar
looked missing when it was only unstyled.

After any structural change, rebuild and run the verification pass in
[`docs/SITE_CONVENTIONS.md`](docs/SITE_CONVENTIONS.md) §3. It has caught a
stale `topic_id` that silently emptied a page's media paths, and a page that
declared `sections` but never included the bar to render them.

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
| `topics.yml` | the science topics: cards, topic bar, and each topic page's header |
| `work_packages.yml` | WP1–WP3 and their lettered tasks |
| `people.yml` | PI, team members, external collaborators |
| `positions.yml` | **open calls only** — never what the project plans to recruit |
| `publications.yml` | papers and talks that acknowledge the grant |
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

The topic list is flat on purpose. An earlier version grouped it, which was
wrong: microlensing is a wave-optics problem, a search problem and a
dark-matter probe at once, so any partition misleads.

### Animations

Topic-page animations live in `media/` as `<topic>.webm`, `<topic>.mp4` and
`<topic>_still.png`. They are **not** generated here — each comes from the repo
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
