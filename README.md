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
browser shows.

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
| `work_packages.yml` | WP1–WP3 and their lettered tasks |
| `people.yml` | PI, team members, external collaborators |
| `positions.yml` | funded positions; set `status: open` only when a call is live |
| `news.yml` | dated one-sentence items for the home page |
| `software.yml` | tools and the release policy |

Site-wide facts — grant number, host institution, the EU funding statement —
live in `_config.yml` so they cannot drift between pages.

## EU funding obligation

The emblem and the words "Funded by the European Union", together with the
disclaimer, appear in the footer of every page, driven by the `eu:` block in
`_config.yml`. Do not remove them, and do not alter the emblem image: the
supplied file is the white-wordmark variant the emblem rules require on a dark
background.
