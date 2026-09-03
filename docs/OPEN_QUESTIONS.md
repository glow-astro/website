# Open design questions

Deliberately unresolved, with the reasoning that got them here. Each is a
judgement call the owner has parked, not a bug and not an oversight — so the
useful thing to record is what was already tried, what was already rejected, and
what would change the answer.

Decided questions do not belong here; they belong in the code comment or the
commit message at the place they affect. Two questions live elsewhere because
they are large enough to need their own file:
`NAMESPACE_AND_REDIRECTS.md` holds the GLoW repository-location decision and
the domain choice. That file is kept locally and untracked, so it is beside
this one on the owner's machine and not in the repository.

---

## The submenu on `science.html`

*Raised 2026-08-16, after the source–lens–observer diagram became the Topics
section (`fd6fba9`).*

`science.html` is **the only page in the site that renders both bars**: the
topic bar (`_includes/topicnav.html` — Overview plus the six topics) and the
in-page section bar (`_includes/subnav.html` — Lensing again · Why coherence
changes things · Topics · Why now · What GLOW will deliver). Both are
`position: sticky` and stack under the header via `--header-h` / `--topicnav-h`,
so the page carries three levels of chrome above its content.

That contradicts a decision already written into `_includes/topicnav.html`,
whose comment says the topic bar *"replaces the per-page section bar on topic
pages rather than sitting above it. Three levels of navigation on a short page
is more chrome than content."* The five topic pages follow that rule. The hub
does not.

The owner had said of this bar: *"the topic bar under 'science' is fine,
although not necessary given that the section isn't very lengthy."* It has since
grown a large figure, which changes the balance again — the page now leads with
a diagram that is itself a navigation surface, so a second device pointing at
the same six destinations may be redundant.

**Options when this is picked up:** drop the subnav from `science.html`; drop
the topicnav there, since the diagram already links every topic; or shorten the
section list.

**Already tried and rejected:** adding headings to the topic bar as a grouping
device. Do not re-propose it — the reasons are in the header of
`_data/topics.yml` and in `topicnav.html`.

---

## Figure consistency across the site

*Raised 2026-08-18. The owner asked that this be recorded and explicitly **not**
acted on now. Do not start it unprompted.*

The site's figures come from different scripts in `~/code/application_plots`,
each carrying its own conventions, so they are not consistent with one another.
Three static plots and five animations now sit on the same dark pages, which is
what makes the differences read as sloppiness rather than as separate figures.

What is known to differ:

- **Type sizing.** Only `utils/microlensing_master.py` derives its point sizes
  from the site's CSS pixel scale (`SITE_PX`, `SITE_COLUMN_PX`, `_pt()`), and
  only since the 2026-08-18 fix that measures the tight-cropped width rather
  than the canvas. `utils/pbh_em_panel.py` uses hard-coded points — labels 14,
  ticks 12 — and the population and animation families have their own again.
  They happen to land in the same 15–21 px band on screen; nothing enforces it.
- **Nothing is shared.** There is no common style module for the `_web_dark`
  variants; `utils/sty_*.mplstyle` covers the talk and proposal styles only.
- **Palette, panel framing and scale-bar treatment** have not been compared at
  all.

**Why it is worth doing eventually, and cheaply now:** the site is dark-only and
unpublished, so this is one fix rather than a per-figure tax forever.

**The shape of the fix:** a shared `_web_dark` style module in
`application_plots/utils/` that owns the CSS-derived type scale and the dark
palette, imported by each figure script, with every affected render retaken —
under **new filenames** if the site is live by then, per the cache rule in
`SITE_CONVENTIONS.md` §3.
