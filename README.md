# Ads and Recommendation Training Data Reader

A complete beginner guide to the data that goes into advertising and recommendation models. Follow one impression from raw events to a joined training record and an encoded model batch.

Live site: https://ads-recommendation-data-reader.vercel.app

## Read

- [Guide source](GUIDE.md)
- [Glossary](GLOSSARY.json)
- [Claude review and scope](reviews/claude-review.md)
- Companion: [Computational Advertising Reader](https://github.com/qiaokan/computational-advertising-reader)

The reader has nine chapters, a searchable glossary, a three-stage data inspector, printable chapters, mobile navigation, and deep links. Published Criteo and DIN samples are distinguished from synthetic teaching data.

## Local preview

```sh
python3 -m http.server 8000 --directory dist
```

Open http://localhost:8000. The committed static output needs no install step, network libraries, accounts, database, or runtime API.

## Rebuild

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build.py
```

GUIDE.md and GLOSSARY.json are the content sources. scripts/build.py builds the HTML and copies downloadable content and review files. The CSS and browser JavaScript live in dist/styles.css and dist/app.js. Rebuild after editing guide, glossary, review files, or the template.

## Browser checks

With Playwright installed in your development environment, start the local server and run:

```sh
node tests/reader.test.cjs
```

Alternatively set PLAYWRIGHT_MODULE to the absolute path of an existing Playwright module. READER_URL selects the test server. CHROMIUM_PATH optionally selects an existing isolated Chromium executable. Install a Playwright browser with `npx playwright install chromium` if none is available. Checks cover label maturation, stable prediction features, exact toy encodings, navigation, glossary search, mobile overflow, print completeness, and local links.

## Deploy

Vercel serves the committed dist directory directly, as configured in vercel.json. There is no build command or install command. Never commit .vercel state, credentials, or environment files.

The original prose and teaching examples are provided for learning. Linked datasets, papers, and third-party code retain their own licenses. No full external dataset is bundled.
