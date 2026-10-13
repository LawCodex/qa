# Qatar — LawCodex (تشريعات دولة قطر)

Qatari legislation as plain Markdown, in Arabic (`ar/`), plus Al Meezan's English
translations (`en/`) where one exists. Part of [LawCodex](https://github.com/LawCodex): one
repository per jurisdiction.

- Source: **Al Meezan — Qatar Legal Portal** (الميزان – البوابة القانونية القطرية),
  [almeezan.qa](https://almeezan.qa), run by the Ministry of Justice of the State of Qatar.
  The data comes from the portal's public JSON API (`https://api.moj.gov.qa/api/v1/Legislation/…`),
  the same API the website itself uses.
- Retrieved: **2026-10-13**
- Version: Al Meezan's current text of each instrument. Amended articles appear in their amended
  wording, marked "معدلة" (amended). Repealed articles stay in place, marked "ملغاة" (repealed).
  Article footnotes (e.g. "المادة معدلة بـ…") are kept as block quotes. Nothing is summarised or
  translated.

## Coverage

All 9,669 instruments listed by the portal's legislation search, except one record the API did
not return. That makes **9,668 Arabic files** and **94 English files**.

| Directory | Type (Al Meezan) | Arabic | of which repealed | English |
| --- | --- | ---: | ---: | ---: |
| `constitution/` | دستور: the Permanent Constitution (2004) and the Amended Provisional Basic Law (1972, repealed) | 2 | 1 | 1 |
| `laws/<year>/` | قانون: laws | 880 | 270 | 30 |
| `decree-laws/<year>/` | مرسوم بقانون: decree-laws | 202 | 76 | 2 |
| `decrees/<year>/` | مرسوم: decrees (mostly ratifications of treaties) | 2,099 | 39 | 10 |
| `emiri-orders/<year>/` | أمر أميري: Emiri orders | 140 | 9 | 1 |
| `emiri-decisions/<year>/` | قرار أميري: Emiri decisions | 1,617 | 351 | 16 |
| `cabinet-decisions/<year>/` | قرار مجلس الوزراء: Council of Ministers decisions | 1,271 | 153 | 14 |
| `prime-minister-decisions/<year>/` | قرار رئيس مجلس الوزراء: Prime Minister decisions | 374 | 60 | 2 |
| `ministerial-decisions/<year>/` | قرار وزاري: ministerial decisions | 2,124 | 170 | 11 |
| `decisions/<year>/` | قرار: other decisions | 547 | 6 | 4 |
| `public-prosecutor-decisions/<year>/` | قرار النائب العام: Attorney General decisions | 147 | 1 | 0 |
| `other/<type>/<year>/` | 24 smaller types: supreme council and board decisions, rules, articles and memoranda of association of public companies, announcements … | 265 | 10 | 3 |

`status` comes from Al Meezan: قيد التطبيق → `in_force`, ملغى → `repealed`. `repealed_on`
gives the repeal date where one is known.

### English

Al Meezan returns an English record for many instruments. In most of them, only the title is
translated and the articles fall back to Arabic. An `en/` file is written only when at least
half of the articles (or the whole text, if the instrument has no articles) are in English. The
constitution has a few amended articles that are still in Arabic, so they appear in Arabic in its
English file. Al Meezan marks 38 of the English texts as machine-translated. Those files carry
`machine_translated: true`. The Arabic text is the only authoritative one.

### Not covered / known gaps

- One instrument could not be fetched: the API returned errors on every retry.
- Court rulings, legal opinions (fatwas), the separate treaty database, Shura Council
  materials and the "almawad" article cross-reference pages are not included.
- Attached files, such as Official Gazette scans, tables and annexes published only as PDF, are
  not included. Their links remain on each instrument's Al Meezan page.
- Al Meezan's article-level consolidation can lag behind recent amendments. Check the Official
  Gazette for authoritative wording.

## Structure and file names

```
ar/constitution/<year>-constitution.md
ar/<type>/<year>/<year>-<number>.md
en/...  (same layout and file names as ar/)
```

Files are named `<year>-<number>.md` after the instrument's official number and year. Several
ministries may number their decisions independently, so if two instruments of the same type
share a number and year, the issuer's code is appended (e.g. `1981-5-interior-minister.md`).
If that still leaves two files with the same name, the Al Meezan id prefix is appended as well.

Front matter: `title` (official Arabic or English title), `identifier` (Al Meezan's canonical
path `/legislations/<type>/<year>/<number>/<issuer>`), `almeezan_id` (GUID), `type`, `number`,
`year`, `date` (issue date), `date_hijri`, `effective`, `status`, `repealed_on`, `gazette`
(Official Gazette issue and pages), `issuer`, `source`, `retrieved`.

The body starts with the preamble (the issuing formula: "نحن تميم بن حمد آل ثاني …"). Then come
Al Meezan's sections (الباب / الفصل …) as headings and the articles (مادة N) as the deepest
headings, followed by the signatures.

## Licence

These are official texts of the State of Qatar. Under Article 4(1) of Qatar's copyright law (Law No. 7 of 2002 on
the Protection of Copyright and Neighbouring Rights,
[`ar/laws/2002/2002-7.md`](ar/laws/2002/2002-7.md)), "legislation, judicial rulings, decisions
of administrative bodies, international agreements and all other official documents, as well as
their official translations" are not protected. The Al Meezan
portal does not publish any terms of use that restrict reuse, and its robots.txt allows all
crawling.

## Regenerating

```sh
pip install -r scripts/requirements.txt
python scripts/qa_fetch.py  /path/to/raw     # listing + one JSON per instrument (cached)
python scripts/qa_convert.py /path/to/raw .  # writes ar/ and en/
```

The fetcher uses at most three parallel connections, pauses between requests, and identifies
itself as `LawCodex/1.0`.
