"""Build the static reader from its public Markdown source. No runtime dependencies."""
from pathlib import Path
import html
import json
import re
import shutil
import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
OUT.mkdir(exist_ok=True)
source = (ROOT / 'GUIDE.md').read_text()
parts = []
in_fence = False
for line in source.splitlines(keepends=True):
    if line.startswith('```'):
        in_fence = not in_fence
    if line.startswith('# ') and not in_fence:
        parts.append(line[2:])
    elif parts:
        parts[-1] += line
parts = parts[1:]  # Native page title is rendered by the reader shell.
chapters = []
nav = []
for i, part in enumerate(parts):
    title, _, body = part.partition('\n')
    slug = f'chapter-{i + 1}'
    rendered = markdown.markdown('## ' + title + '\n' + body, extensions=['fenced_code', 'tables', 'toc'])
    rendered = re.sub(r'<pre><code class="language-mermaid">.*?</code></pre>', '''<div class="pipeline" aria-label="Training data pipeline"><span>Raw events</span><b aria-hidden="true">→</b><span>Training records</span><b aria-hidden="true">→</b><span>Encoded batches</span><b aria-hidden="true">→</b><span>Model + labels</span></div>''', rendered, flags=re.S)
    chapters.append(f'<section class="chapter" id="{slug}" data-title="{html.escape(title, quote=True)}"><p class="eyebrow">CHAPTER {i + 1:02d}</p>{rendered}</section>')
    nav.append(f'<a href="#{slug}" data-chapter="{i}"><span>{i + 1:02d}</span>{html.escape(title)}</a>')

glossary_path = ROOT / 'GLOSSARY.json'
glossary = json.loads(glossary_path.read_text()) if glossary_path.exists() else []
terms = ''.join(f'<div class="term" data-term="{html.escape(t["term"].lower(), quote=True)}"><dt>{html.escape(t["term"])}</dt><dd>{html.escape(t["definition"])}</dd></div>' for t in glossary)
glossary_index = len(chapters)
nav.append(f'<a href="#glossary" data-chapter="{glossary_index}"><span>A</span>Glossary and self check</a>')
chapters.append(f'''<section class="chapter" id="glossary" data-title="Glossary and self check"><p class="eyebrow">REFERENCE</p><h2>Glossary and self check</h2><p>Definitions for every technical term you need to follow the guide. Filter by a term or phrase.</p><label for="glossary-search">Find a definition</label><input type="search" id="glossary-search" placeholder="Try embedding, attribution, or calibration"><p id="term-count" role="status"></p><dl id="glossary-list">{terms}</dl><h3>Check your understanding</h3><details><summary>Is an item that was never shown a negative CTR example?</summary><p>No. There is no observed response to that showing. Retrieval may use sampled unobserved items as contrasts, which is a different objective.</p></details><details><summary>Does item ID 100 have twice the meaning of item ID 50?</summary><p>No. IDs identify categories. They are embedding indices, not measurements.</p></details><details><summary>Can the current click appear in the history used to predict it?</summary><p>No. That puts the answer into the features and leaks future information.</p></details><details><summary>Is the label passed to the model at serving time?</summary><p>No. The model receives features. The outcome is not yet known.</p></details><details><summary>Can a one-hour-old impression be a final negative for a seven-day conversion target?</summary><p>No. Its conversion window is still open. Wait, mask it, or use a method that handles delayed outcomes.</p></details></section>''')

inspector = '''<aside class="inspector" aria-labelledby="inspector-heading"><div class="inspector-top"><div><p class="eyebrow">WORKED EXAMPLE · SYNTHETIC</p><h2 id="inspector-heading">Follow one impression</h2></div><span class="badge">U7 × A42</span></div><p>Same user, candidate, and context. Change when the outcome is known and inspect each representation.</p><div class="lab-controls"><label>Outcome state<select id="outcome"><option value="clicked">Clicked within the window</option><option value="not-clicked">No click after the window</option><option value="pending">Observation window still open</option></select></label><label>Representation<select id="representation"><option value="raw">Raw impression</option><option value="record">Training record</option><option value="tensor">Encoded batch</option></select></label></div><p id="inspector-note" role="status"></p><pre><code id="inspector-output"></code></pre><p class="lab-footnote">Encodings are declared teaching values, not a trained model. The label is separate from the features.</p></aside>'''

template = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Learn exactly what goes into an ads or recommendation model: raw logs, training records, embeddings, history sequences, labels and tensors. A complete beginner guide with published examples."><meta name="theme-color" content="#1c3b3c"><title>Ads and Recommendation Training Data — A Beginner Reader</title><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="styles.css"><script src="app.js" defer></script></head>
<body><a class="skip" href="#reading">Skip to the guide</a><header><a class="brand" href="#chapter-1"><span class="brandmark">D</span>THE DATA READER</a><nav aria-label="Project links"><a href="https://computational-advertising-reader.vercel.app">Advertising reader ↗</a><a href="https://github.com/qiaokan/ads-recommendation-data-reader">GitHub ↗</a></nav></header>
<main><div class="hero"><div><p class="eyebrow">ADS & RECOMMENDATIONS / FROM FIRST PRINCIPLES</p><h1>What goes<br>into the model?</h1><p class="lede">From a person seeing an ad to the numbers a neural network learns from. One complete example, every important definition, and real published data.</p><div class="hero-links"><a class="primary" href="#chapter-1">Start reading <span aria-hidden="true">→</span></a><a href="GUIDE.md" download>Download the guide ↓</a></div></div><div class="hero-aside"><strong>01</strong><span>impression followed end to end</span><strong>09</strong><span>chapters, plus a glossary</span><strong>0</strong><span>recommendation background required</span></div></div>
<div class="intro-strip"><span>RAW EVENTS</span><b aria-hidden="true">→</b><span>TRAINING RECORDS</span><b aria-hidden="true">→</b><span>MODEL TENSORS</span><p>Three representations.<br>The same prediction problem.</p></div>
INSPECTOR
<div class="reader-layout"><aside class="toc"><button id="menu-toggle" type="button" aria-expanded="false" aria-controls="chapter-nav">Contents <span aria-hidden="true">☰</span></button><div id="chapter-nav"><p class="eyebrow">YOUR READING PATH</p><nav aria-label="Chapters">NAV</nav><div class="reading-tools"><button id="print-guide" type="button">Print or save as PDF</button><a href="reviews/claude-review.md">Claude review record ↗</a></div></div></aside><div id="reading" tabindex="-1"><div class="reading-bar"><span id="current-chapter">CHAPTER 01</span><span id="reading-progress">1 / 10</span></div><div class="progress-track"><div id="progress-fill"></div></div>CHAPTERS<div class="pagination"><button id="previous" type="button">← Previous</button><span id="page-title"></span><button id="next" type="button">Next →</button></div></div></div>
<footer><p>Examples are synthetic unless explicitly attributed. Real samples link to their original files.</p><p><a href="GUIDE.md">Guide source</a> · <a href="https://github.com/qiaokan/ads-recommendation-data-reader">Source repository</a> · <a href="reviews/claude-review.md">Review scope</a></p></footer></main></body></html>'''
page = template.replace('INSPECTOR', inspector).replace('NAV', ''.join(nav)).replace('CHAPTERS', '\n'.join(chapters))
(OUT / 'index.html').write_text(page)
for filename in ['GUIDE.md', 'GLOSSARY.json']:
    if (ROOT / filename).exists(): shutil.copy(ROOT / filename, OUT / filename)
(OUT / 'reviews').mkdir(exist_ok=True)
for review in (ROOT / 'reviews').glob('*.md'):
    shutil.copy(review, OUT / 'reviews' / review.name)
print(f'Built {len(chapters)} chapters and {len(glossary)} glossary entries.')
