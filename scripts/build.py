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
def term_slug(name):
    return 'term-' + re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

term_ids = {t['term']: term_slug(t['term']) for t in glossary}
assert len(set(term_ids.values())) == len(term_ids), 'Glossary term slugs must be unique.'
categories = sorted({t.get('category', 'Basics') for t in glossary}, key=lambda c: (c != 'Basics', c))

def render_term(t):
    esc = lambda text: html.escape(text).replace('\n', '<br>')
    category = t.get('category', 'Basics')
    body = [f'<p class="term-def">{esc(t["definition"])}</p>']
    if t.get('details'):
        body.append(f'<p>{esc(t["details"])}</p>')
    if t.get('example'):
        body.append(f'<p class="term-example"><strong>Example</strong> {esc(t["example"])}</p>')
    if t.get('pitfall'):
        body.append(f'<p class="term-pitfall"><strong>Watch out</strong> {esc(t["pitfall"])}</p>')
    related = [r for r in t.get('related', []) if r in term_ids]
    if related:
        links = ', '.join(f'<a href="#{term_ids[r]}">{html.escape(r)}</a>' for r in related)
        body.append(f'<p class="term-related">See also: {links}</p>')
    return (f'<div class="term" id="{term_ids[t["term"]]}" data-term="{html.escape(t["term"].lower(), quote=True)}" data-category="{html.escape(category, quote=True)}">'
            f'<dt><span class="term-name">{html.escape(t["term"])}</span><span class="term-tag">{html.escape(category)}</span></dt>'
            f'<dd>{"".join(body)}</dd></div>')

terms = ''.join(render_term(t) for t in glossary)
category_buttons = '<button type="button" class="category-filter" data-category="" aria-pressed="true">All</button>' + ''.join(
    f'<button type="button" class="category-filter" data-category="{html.escape(c, quote=True)}" aria-pressed="false">{html.escape(c)}</button>' for c in categories)
glossary_index = len(chapters)
nav.append(f'<a href="#glossary" data-chapter="{glossary_index}"><span>A</span>Glossary and self check</a>')
glossary_html = f'''<section class="chapter" id="glossary" data-title="Glossary and self check"><p class="eyebrow">REFERENCE</p><h2>Glossary and self check</h2><p>Every technical term in the guide, explained so you do not need to look anything up elsewhere. Each entry starts with a one-line definition, then explains why it matters, works through a concrete example (mostly the same U7 / A42 impression used in the chapters), flags common mistakes, and links to related terms.</p><label for="glossary-search">Find a definition</label><input type="search" id="glossary-search" placeholder="Try embedding, attribution, or calibration"><div class="category-filters" role="group" aria-label="Filter by topic">CATEGORY_BUTTONS</div><p id="term-count" role="status"></p><dl id="glossary-list">{terms}</dl><h3>Check your understanding</h3><details><summary>Is an item that was never shown a negative CTR example?</summary><p>No. There is no observed response to that showing. Retrieval may use sampled unobserved items as contrasts, which is a different objective.</p></details><details><summary>Does item ID 100 have twice the meaning of item ID 50?</summary><p>No. IDs identify categories. They are embedding indices, not measurements.</p></details><details><summary>Can the current click appear in the history used to predict it?</summary><p>No. That puts the answer into the features and leaks future information.</p></details><details><summary>Is the label passed to the model at serving time?</summary><p>No. The model receives features. The outcome is not yet known.</p></details><details><summary>Can a one-hour-old impression be a final negative for a seven-day conversion target?</summary><p>No. Its conversion window is still open. Wait, mask it, or use a method that handles delayed outcomes.</p></details></section>'''
chapters.append(glossary_html.replace('CATEGORY_BUTTONS', category_buttons))

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
