#!/usr/bin/env python3
"""Collect candidates for the "papers using <code>" lists, from INSPIRE.

    python3 tools/fetch_code_papers.py            # every tool with seeds
    python3 tools/fetch_code_papers.py glow       # one tool

Reads `inspire_seeds` from each tool in _data/software.yml, asks INSPIRE for
everything citing those records, and merges the result into
_data/code_papers.yml.

WHAT THIS TOOL DOES NOT DO

It does not decide whether a paper used the code. A citation is not a use: of
the 74 papers citing the GLoW method paper, plenty cite it for the physics and
never ran it, and INSPIRE has no field that would tell them apart. Abstracts do
not help either -- not one of those 74 names GLoW in its abstract, which was
checked before this tool was written rather than assumed.

So every new candidate arrives with `include: null`, meaning "nobody has looked
yet", and the page renders only `include: true`. A refresh never overwrites a
decision and never deletes an entry, so running this repeatedly is safe and the
curation survives. That is the whole design: the network gives breadth, a human
gives truth.

Only the network-facing fields are refreshed on a re-run (title, authors,
journal, date), because those improve as INSPIRE learns a paper's publication
details. `include` and `codes` are yours and are left alone.

No dependencies beyond the standard library and PyYAML, which the other tools
in here already need.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOFTWARE = ROOT / "_data" / "software.yml"
PAPERS = ROOT / "_data" / "code_papers.yml"

API = "https://inspirehep.net/api/literature"
FIELDS = ("titles,authors,arxiv_eprints,publication_info,earliest_date,"
          "dois,control_number,collaborations")
# INSPIRE asks for a contactable agent. The address identifies the site, and
# goes nowhere else.
AGENT = "glow-erc-website/1.0 (https://glow-astro.org; miguelzuma@gmail.com)"


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=60) as fh:
        return json.load(fh)


def citing(recid: int) -> list[dict]:
    """Every record citing `recid`, following INSPIRE's pagination."""
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "q": f"refersto recid {recid}", "size": 100,
            "page": page, "fields": FIELDS, "sort": "mostrecent",
        })
        hits = _get(f"{API}?{q}")["hits"]["hits"]
        out += hits
        if len(hits) < 100:
            return out
        page += 1
        time.sleep(0.3)


def _authors(meta: dict) -> str:
    """Initial-and-surname, in the paper's own order, "et al." past three.

    The shape hi_class uses on its publication list, and short enough that an
    entry stays on one line at the site's measure.
    """
    if meta.get("collaborations"):
        return meta["collaborations"][0].get("value", "") + " Collaboration"
    names = []
    for a in meta.get("authors", [])[:4]:
        full = a.get("full_name", "")
        surname, _, given = full.partition(", ")
        initials = " ".join(f"{p[0]}." for p in given.replace("-", " ").split() if p)
        names.append(f"{initials} {surname}".strip())
    if len(meta.get("authors", [])) > 3:
        return ", ".join(names[:3]) + " et al."
    return ", ".join(names)


def _journal(meta: dict) -> str | None:
    for info in meta.get("publication_info", []):
        title = info.get("journal_title")
        if not title:
            continue
        vol, page = info.get("journal_volume"), info.get("page_start")
        year = info.get("year")
        ref = title + (f" {vol}" if vol else "")
        if page:
            ref += f", {page}"
        if year:
            ref += f" ({year})"
        return ref
    return None


# INSPIRE titles carry TeX and this site renders no maths, so "$10-10^4\\,{\\rm
# M}_{\\odot}$" would reach the page verbatim. _data/publications.yml writes the
# same thing as "10-10⁴ M☉" by hand; this converts the cases that actually turn
# up in a lensing bibliography and leaves the rest visible, because a title that
# still holds a backslash is a title a human has to look at.
_SYMBOLS = {
    r"\odot": "☉", r"\sim": "~", r"\times": "×", r"\pm": "±",
    r"\rightarrow": "→", r"\to": "→", r"\approx": "≈",
    r"\lesssim": "≲", r"\gtrsim": "≳", r"\ll": "≪", r"\gg": "≫",
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\mu": "μ",
    r"\nu": "ν", r"\Lambda": "Λ", r"\Omega": "Ω", r"\Delta": "Δ",
    r"\Sigma": "Σ", r"\chi": "χ", r"\Phi": "Φ", r"\phi": "φ",
    r"\deg": "°", r"\%": "%",
}
_SUP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
_SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")


def _detex(text: str) -> str:
    import re as _re
    t = text
    for wrapper in ("mathrm", "mathcal", "mathbf", "textrm", "text", "rm", "bf", "it"):
        t = _re.sub(r"\\" + wrapper + r"\s*\{([^{}]*)\}", r"\1", t)
        t = _re.sub(r"\{\\" + wrapper + r"\s+([^{}]*)\}", r"\1", t)
    for tex, uni in _SYMBOLS.items():
        t = t.replace(tex, uni)
    t = _re.sub(r"_\{?☉\}?", "☉", t)           # M_{\odot} -> M☉, the common one
    t = _re.sub(r"\\[,;!:> ]", " ", t)          # thin spaces and friends
    t = _re.sub(r"\^\{([0-9+\-=()n]+)\}", lambda m: m.group(1).translate(_SUP), t)
    t = _re.sub(r"\^([0-9])", lambda m: m.group(1).translate(_SUP), t)
    t = _re.sub(r"_\{([0-9+\-=()]+)\}", lambda m: m.group(1).translate(_SUB), t)
    t = _re.sub(r"_([0-9])", lambda m: m.group(1).translate(_SUB), t)
    t = t.replace("$", "")
    t = _re.sub(r"\{([^{}]*)\}", r"\1", t)      # leftover grouping braces
    return _re.sub(r"\s+", " ", t).strip()


def _entry(meta: dict) -> dict:
    arx = (meta.get("arxiv_eprints") or [{}])[0].get("value")
    return {
        "arxiv": arx,
        "title": _detex(meta["titles"][0]["title"]),
        "authors": _authors(meta),
        "url": f"https://inspirehep.net/literature/{meta['control_number']}",
        "date": meta.get("earliest_date"),
        "journal": _journal(meta),
    }


def main(argv: list[str]) -> int:
    tools = yaml.safe_load(SOFTWARE.read_text())["tools"]
    wanted = set(argv) or {t["id"] for t in tools if t.get("inspire_seeds")}

    existing = []
    if PAPERS.exists():
        existing = yaml.safe_load(PAPERS.read_text()) or []
    by_key = {p.get("arxiv") or p["url"]: p for p in existing}

    added = 0
    for tool in tools:
        if tool["id"] not in wanted or not tool.get("inspire_seeds"):
            continue
        for recid in tool["inspire_seeds"]:
            for hit in citing(recid):
                new = _entry(hit["metadata"])
                key = new["arxiv"] or new["url"]
                cur = by_key.get(key)
                if cur is None:
                    new["codes"] = [tool["id"]]
                    new["include"] = None
                    by_key[key] = new
                    added += 1
                    continue
                # Refresh only what INSPIRE owns. `codes` and `include` are the
                # human's, and a re-run must never touch them.
                for field in ("title", "authors", "url", "date", "journal"):
                    cur[field] = new[field]
                if tool["id"] not in cur.get("codes", []):
                    cur.setdefault("codes", []).append(tool["id"])
            time.sleep(0.3)

    papers = sorted(by_key.values(), key=lambda p: (p.get("date") or "", p["title"]),
                    reverse=True)
    header = PAPERS.read_text().split("\n\n", 1)[0] + "\n\n" if PAPERS.exists() else ""
    PAPERS.write_text(header + yaml.safe_dump(
        papers, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False))

    messy = [p["arxiv"] for p in papers
             if "\\" in p["title"] or "$" in p["title"] or "^" in p["title"]
             or "_{" in p["title"]]
    if messy:
        print(f"  {len(messy)} titles still hold TeX after conversion, so they need "
              f"a human: {', '.join(str(m) for m in messy[:8])}")

    undecided = sum(1 for p in papers if p.get("include") is None)
    print(f"{PAPERS}: {len(papers)} papers, {added} new, {undecided} awaiting a decision")
    if undecided:
        print("  set `include: true` on the ones that actually used the code; "
              "`false` on the rest. Nothing renders until you do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
