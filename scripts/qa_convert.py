#!/usr/bin/env python3
"""Convert Al Meezan legislation JSON (see qa_fetch.py) to LawCodex Markdown.

Usage: qa_convert.py RAW_DIR REPO_DIR
"""
import collections, datetime, glob, json, os, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag

TODAY = datetime.date.today().isoformat()

# typeCode -> (directory, front-matter type)
DIRS = {
    'constitution': ('constitution', 'constitution'),
    'law': ('laws', 'law'),
    'decree-law': ('decree-laws', 'decree_law'),
    'decree': ('decrees', 'decree'),
    'emiri-order': ('emiri-orders', 'emiri_order'),
    'emiri-decision': ('emiri-decisions', 'emiri_decision'),
    'cabinet-decision': ('cabinet-decisions', 'cabinet_decision'),
    'prime-minister-decision': ('prime-minister-decisions', 'prime_minister_decision'),
    'ministerial-decision': ('ministerial-decisions', 'ministerial_decision'),
    'decision': ('decisions', 'decision'),
    'public-prosecutor-decision': ('public-prosecutor-decisions', 'public_prosecutor_decision'),
}
STATUS = {'قيد التطبيق': 'in_force', 'ملغى': 'repealed', 'In Force': 'in_force', 'Repealed': 'repealed'}


def clean(s):
    return re.sub(r'[ \t\u00a0\u200b]+', ' ', s).strip()


def yq(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ') + '"'


def inline(node):
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            if c.__class__.__name__ in ('Comment', 'Doctype', 'ProcessingInstruction'):
                continue
            out.append(re.sub(r'\s+', ' ', str(c)))
        elif isinstance(c, Tag):
            n = c.name.lower()
            if n.startswith('br'):
                out.append('\n')
                out.append(inline(c))
            elif n in ('script', 'style'):
                continue
            elif n in ('strong', 'b'):
                t = inline(c).strip()
                out.append(f'**{t}**' if t and '\n' not in t and '**' not in t else t)
            elif n == 'table':
                out.append('\n\n' + table(c) + '\n\n')
            elif n in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'center', 'tr', 'blockquote'):
                out.append('\n\n' + inline(c) + '\n\n')
            else:
                out.append(inline(c))
    return ''.join(out)


def table(t):
    rows = []
    for tr in t.find_all('tr'):
        cells = tr.find_all(['td', 'th'], recursive=False)
        if any(c.get('rowspan') or c.get('colspan') for c in cells):
            return html_table(t)
        rows.append([clean(inline(c)).replace('\n', '<br>').replace('|', '\\|') for c in cells])
    rows = [r for r in rows if r]
    if not rows:
        return ''
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    md = ['| ' + ' | '.join(rows[0]) + ' |', '|' + ' --- |' * n]
    md += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(md)


def html_table(t):
    for tag in t.find_all(True):
        keep = {k: v for k, v in tag.attrs.items() if k in ('rowspan', 'colspan')}
        tag.attrs = keep
    return re.sub(r'\s+', ' ', str(t))


def md(html):
    if not html:
        return ''
    s = BeautifulSoup(html, 'lxml')
    root = s.body or s
    lines = [clean(l) for l in inline(root).split('\n')]
    return '\n\n'.join(l for l in lines if l and l != '**' and l != '****')


def depth(secs):
    return max((1 + depth(s['sections']) for s in secs), default=0)


def render_sections(secs, level, art_level, out):
    for s in secs:
        title = clean(s.get('title') or '')
        if title:
            out.append('#' * level + ' ' + title)
        for a in s['almawad']:
            render_article(a, min(level + 1, 6) if title else level, out)
        render_sections(s['sections'], min(level + 1, 6), art_level, out)


def render_article(a, level, out):
    t = clean(a.get('title') or '')
    if t:
        out.append('#' * level + ' ' + t if level <= 6 else f'**{t}**')
    body = md(a.get('description'))
    if body:
        out.append(body)
    note = md(a.get('footerNote'))
    if note:
        out.append('\n>\n'.join('> ' + p for p in note.split('\n\n')))


def latin(text):
    return len(re.findall('[A-Za-z]', text)) > 2 * len(re.findall('[\u0600-\u06FF]', text))


def articles_text(d):
    def walk(secs):
        for s in secs:
            for a in s['almawad']:
                yield (a.get('description') or '') + (a.get('title') or '')
            yield from walk(s['sections'])
    return ' '.join(walk(d['sections'])) or (d.get('description') or '')


def english_share(d):
    """Share of articles whose text is in English (untranslated articles fall back to Arabic)."""
    arts = []

    def walk(secs):
        for s in secs:
            arts.extend(re.sub('<[^>]+>', ' ', a.get('description') or '') for a in s['almawad'])
            walk(s['sections'])
    walk(d.get('sections') or [])
    if not arts:
        return 1.0 if latin(re.sub('<[^>]+>', ' ', d.get('description') or '')) else 0.0
    return sum(1 for a in arts if latin(a)) / len(arts)


def date(s):
    return s[:10] if s else None


def build(d, lang, rel_dir, slug):
    title = clean(d.get('titleClear') or d.get('title') or '')
    status = STATUS.get(d.get('status'), 'unknown')
    fm = ['---', f'title: {yq(title)}', f'identifier: {yq(d.get("legislationURL") or d["id"])}',
          f'almeezan_id: {yq(d["id"])}',
          f'type: {DIRS.get(d["typeCode"], (None, d["typeCode"].replace("-", "_")))[1]}',
          'jurisdiction: qa', f'language: {lang}', f'number: {yq(d.get("number") or "")}',
          f'year: {d.get("year")}']
    if date(d.get('publishDate')):
        fm.append(f'date: {date(d["publishDate"])}')
    if d.get('publishDateHijri'):
        fm.append(f'date_hijri: {yq(d["publishDateHijri"])}')
    if date(d.get('effectiveDate')):
        fm.append(f'effective: {date(d["effectiveDate"])}')
    fm.append(f'status: {status}')
    if date(d.get('cancelationDate')):
        fm.append(f'repealed_on: {date(d["cancelationDate"])}')
    og = d.get('officialGazette')
    if og and og.get('title'):
        g = og['title']
        if og.get('pageFrom'):
            g += f', p. {og["pageFrom"]}' + (f'-{og["pageTo"]}' if og.get('pageTo') and og['pageTo'] != og['pageFrom'] else '')
        fm.append(f'gazette: {yq(g)}')
    fm.append(f'issuer: {yq(d.get("sourceCode") or "")}')
    fm.append(f'source: {yq("https://almeezan.qa/legislations/" + d["id"])}')
    fm.append(f'retrieved: {TODAY}')
    if lang == 'en' and d.get('isMachineTranslated'):
        fm.append('machine_translated: true')
    if lang == 'en':
        fm.append('translation: "English translation published by Al Meezan (Ministry of Justice); the Arabic text is authoritative"')
    fm.append('---')
    out = []
    pre = md(d.get('description'))
    if pre and clean(pre) != title:
        out.append(pre)
    secs = d.get('sections') or []
    dp = depth(secs)
    render_sections(secs, 2, min(2 + dp, 6) if dp else 2, out)
    # signatures
    for s in d.get('signatures') or []:
        sig = ' — '.join(x for x in (clean(s.get('name') or ''), clean(s.get('position') or '')) if x)
        if sig:
            out.append(sig)
    return '\n'.join(fm) + '\n\n# ' + title + '\n\n' + '\n\n'.join(out).strip() + '\n'


def main():
    raw, repo = sys.argv[1], sys.argv[2]
    docs = {}
    for f in glob.glob(os.path.join(raw, 'json', '*_ar.json')):
        d = json.load(open(f))
        docs[d['id']] = d
    plan, used = {}, collections.Counter()
    for lid, d in docs.items():
        tc = d['typeCode'] or 'other'
        sub = DIRS[tc][0] if tc in DIRS else f'other/{tc}'
        year = str(d.get('year') or 'unknown')
        num = re.sub(r'[^0-9a-z]+', '-', str(d.get('number') or '').lower()).strip('-') or 'nn'
        rel = sub if tc == 'constitution' else f'{sub}/{year}'
        if tc == 'constitution':
            num = 'constitution'
        plan[lid] = [rel, f'{year}-{num}', d.get('sourceCode') or '']
        used[(rel, f'{year}-{num}')] += 1
    used2 = collections.Counter()
    for lid, p in plan.items():
        if used[(p[0], p[1])] > 1 and p[2] and p[2] != 'general':
            p[1] = f'{p[1]}-{p[2]}'[:90]
        used2[(p[0], p[1])] += 1
    for lid, p in plan.items():
        if used2[(p[0], p[1])] > 1:
            p[1] = f'{p[1]}-{lid[:8]}'
    counts = collections.Counter()
    for lid, d in docs.items():
        rel, slug, _ = plan[lid]
        langs = [('ar', d)]
        fen = os.path.join(raw, 'json', f'{lid}_en.json')
        if os.path.exists(fen):
            de = json.load(open(fen))
            if english_share(de) >= 0.5 and latin(de.get('title') or ''):
                langs.append(('en', de))
        for lang, dd in langs:
            text = build(dd, lang, rel, slug)
            path = os.path.join(repo, lang, rel, slug + '.md')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text)
            counts[(lang, rel.split('/')[0] if not rel.startswith('other') else 'other',
                    STATUS.get(dd.get('status'), 'unknown'))] += 1
    for k in sorted(counts):
        print(*k, counts[k])


if __name__ == '__main__':
    main()
