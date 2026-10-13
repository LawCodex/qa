#!/usr/bin/env python3
"""Fetch Qatari legislation from the Al Meezan public API (api.moj.gov.qa, used by almeezan.qa).

Usage: qa_fetch.py RAW_DIR
  RAW_DIR/list_ar.json, list_en.json   full listing (Legislation/search)
  RAW_DIR/json/<id>_<lang>.json         legislation details (sections, articles, metadata)
"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests

API = 'https://api.moj.gov.qa/api/v1'
UA = 'LawCodex/1.0 (+https://github.com/LawCodex)'
LANGNUM = {'ar': '2', 'en': '1'}


def session():
    s = requests.Session()
    s.headers['User-Agent'] = UA
    return s


S = session()


def get(path, lang, timeout=90):
    sep = '&' if '?' in path else '?'
    url = f'{API}{path}{sep}lang={LANGNUM[lang]}'
    delay = 5
    for attempt in range(8):
        try:
            r = S.get(url, headers={'Accept-Language': lang}, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            print('  HTTP', r.status_code, url, file=sys.stderr, flush=True)
        except (requests.RequestException, ValueError) as e:
            print('  ERR', type(e).__name__, url, file=sys.stderr, flush=True)
        time.sleep(delay)
        delay = min(delay * 2, 120)
    return None


def listing(raw, lang):
    path = os.path.join(raw, f'list_{lang}.json')
    if os.path.exists(path):
        return json.load(open(path))
    items, page = [], 1
    while True:
        d = get(f'/Legislation/search?pageNumber={page}&pageSize=100', lang)['data']
        items += d['data']
        print(lang, 'page', page, '/', d['totalPages'], flush=True)
        if not d['hasNextPage']:
            break
        page += 1
        time.sleep(0.5)
    json.dump(items, open(path, 'w'), ensure_ascii=False)
    return items


def latin(s):
    return bool(s) and len(re.findall('[A-Za-z]', s)) > len(re.findall('[؀-ۿ]', s))


def fetch(item):
    lid, lang = item
    out = os.path.join(RAW, 'json', f'{lid}_{lang}.json')
    if os.path.exists(out):
        return
    d = get(f'/Legislation/{lid}', lang)
    if d is None:
        print('MISSING', lid, lang, flush=True)
        return
    json.dump(d['data'], open(out, 'w'), ensure_ascii=False)
    time.sleep(0.3)


def main():
    global RAW
    RAW = sys.argv[1]
    os.makedirs(os.path.join(RAW, 'json'), exist_ok=True)
    ar = listing(RAW, 'ar')
    en = listing(RAW, 'en')
    jobs = [(x['id'], 'ar') for x in ar]
    jobs += [(x['id'], 'en') for x in en if latin(x.get('title'))]
    print(len(ar), 'legislations;', len(jobs) - len(ar), 'with an English title', flush=True)
    done = 0
    with ThreadPoolExecutor(3) as ex:
        for _ in ex.map(fetch, jobs):
            done += 1
            if done % 200 == 0:
                print('done', done, '/', len(jobs), flush=True)


if __name__ == '__main__':
    main()
