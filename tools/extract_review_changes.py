#!/usr/bin/env python3
"""Read tracked changes and comments out of the review .odt as a plain report.

    python3 tools/extract_review_changes.py <unzipped content.xml>
    ACCEPT=1 python3 tools/extract_review_changes.py <content.xml>   # changes applied
    LO=220 HI=240 python3 ...                                        # a paragraph range

The counterpart to make_review_doc.py: that script writes the document the
owner edits, this one reads their edits back out. Diff one round's report
against the previous round's to see what is new.

Reading the report is not by itself enough. Edits made with track changes
switched off leave no marker at all, so also render the owner's copy with
ACCEPT=1 and diff it against a freshly generated baseline -- that is the only
way untracked edits surface.
"""
import sys, os, xml.etree.ElementTree as ET
ACCEPT = os.environ.get('ACCEPT') == '1'

NS = {
 'office':'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
 'text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
 'dc':'http://purl.org/dc/elements/1.1/',
}
def q(t):
    p,l = t.split(':'); return '{%s}%s' % (NS[p], l)

tree = ET.parse(sys.argv[1]); root = tree.getroot()
body = root.find(q('office:body')).find(q('office:text'))

def plain(el):
    """All text under el, ignoring change markers."""
    out = []
    def walk(n):
        if n.tag == q('office:annotation'): return
        if n.text: out.append(n.text)
        for c in n:
            walk(c)
            if c.tail: out.append(c.tail)
    walk(el)
    return ''.join(out)

# change-id -> (kind, author, deleted-text)
regions = {}
tc = body.find(q('text:tracked-changes'))
for cr in (tc.findall(q('text:changed-region')) if tc is not None else []):
    cid = cr.get(q('text:id')) or cr.get('{http://www.w3.org/XML/1998/namespace}id')
    ins = cr.find(q('text:insertion')); dele = cr.find(q('text:deletion'))
    fmt = cr.find(q('text:format-change'))
    kind = 'ins' if ins is not None else ('del' if dele is not None else 'fmt')
    node = ins if ins is not None else (dele if dele is not None else fmt)
    if node is None:
        regions[cid] = ('?', '?', ''); continue
    ci = node.find(q('office:change-info'))
    author = ci.findtext(q('dc:creator')) if ci is not None else '?'
    dtext = ''
    if dele is not None:
        # Deleted content is <text:p> for prose and <text:h> for a heading;
        # reading only the first loses every deleted heading silently.
        parts = [plain(c).strip() for c in dele
                 if c.tag in (q('text:p'), q('text:h'))]
        dtext = ' '.join(x for x in parts if x)
    regions[cid] = (kind, author, dtext)


def blocks(root):
    """text:p / text:h in document order, including those nested in lists."""
    for c in root:
        if c.tag == q('text:tracked-changes'):
            continue
        if c.tag in (q('text:p'), q('text:h')):
            yield c
        elif c.tag in (q('text:list'), q('text:list-item'),
                       q('text:list-header'), q('text:section')):
            for x in blocks(c):
                yield x

SAW = [False]

# An insertion may open in one paragraph and close two paragraphs later. The
# paragraphs in between carry no change marker of their own, so if this state
# were local to render() they would look untouched and vanish from the report --
# which is exactly how a paragraph of the owner's prose was missed once.
OPEN = []

def render(el):
    """Paragraph text with {-deleted-} and {+inserted+} markers."""
    out = []; open_ins = OPEN
    started_open = bool(OPEN)          # an insertion carried in from an earlier paragraph
    SAW[0] = started_open
    if el.text: out.append(el.text)
    if started_open and not ACCEPT:
        out.insert(0, '{+')
    def walk(n):
        if n.tag == q('office:annotation'):
            who = n.findtext(q('dc:creator')) or '?'
            txt = ' '.join(plain(p).strip() for p in n.findall(q('text:p')))
            out.append('  <<COMMENT [%s]: %s>>  ' % (who, txt)); return
        if n.tag == q('text:change-start'):
            cid = n.get(q('text:change-id'))
            if regions.get(cid, ('',))[0] == 'ins':
                SAW[0] = True
                if not ACCEPT: out.append('{+')
                open_ins.append(cid)
        elif n.tag == q('text:change-end'):
            if open_ins:
                if not ACCEPT: out.append('+}')
                open_ins.pop()
        elif n.tag == q('text:change'):
            cid = n.get(q('text:change-id'))
            k, a, d = regions.get(cid, ('?','?',''))
            if d:
                SAW[0] = True
                if not ACCEPT: out.append('{-%s-}' % d)
        elif n.tag == q('text:s'):
            out.append(' ')
        else:
            if n.text: out.append(n.text)
            for c in n:
                walk(c)
                if c.tail: out.append(c.tail)
            return
        if n.text: out.append(n.text)
        for c in n:
            walk(c)
            if c.tail: out.append(c.tail)
    for c in el:
        walk(c)
        if c.tail: out.append(c.tail)
    if OPEN and not ACCEPT:
        out.append('+}')   # still open; closes in a later paragraph
    return ''.join(out)

import os as _os
LO = int(_os.environ.get('LO', 0)); HI = int(_os.environ.get('HI', 10**9))
heading = source = ''
n = 0
idx = 0
for el in blocks(body):
    idx += 1
    txt = render(el)
    flat = plain(el).strip()
    if el.tag == q('text:h'):
        heading = flat
    if flat.startswith('SOURCE'):
        source = flat
    touched = SAW[0] or ('<<COMMENT' in txt and 'meta name' not in txt)
    if LO: touched = (LO <= idx <= HI)
    if touched:
        n += 1
        print('    (para %d)' % idx, end='')
        print('\n--- [%d] %s' % (n, heading))
        if source: print('    %s' % source)
        print('    %s' % ' '.join(txt.split()))
print('\n== %d paragraphs touched ==' % n)
