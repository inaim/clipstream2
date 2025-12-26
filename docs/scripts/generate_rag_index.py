#!/usr/bin/env python3
"""Generate RAG_INDEX.json from docs/ directory.
Collects title, summary, topics (from headings), metadata block (HTML comment), and source links.
"""
import os
import re
import json
from datetime import datetime

REPO_URL = "https://github.com/inaim/clipstream2/blob/main"
DOCS_DIR = os.path.join(os.path.dirname(__file__), '..')
IGNORE_DIRS = {'archive', '__pycache__'}

md_files = []
for root, dirs, files in os.walk(DOCS_DIR):
    # skip archive and pycache
    parts = os.path.relpath(root, DOCS_DIR).split(os.sep)
    if any(p in IGNORE_DIRS for p in parts):
        continue
    for f in files:
        if f.endswith('.md'):
            md_files.append(os.path.join(root, f))

entries = []

def extract_metadata_and_content(path):
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    metadata = {}
    # HTML comment metadata block at the top
    m = re.match(r'<!--\s*(.*?)\s*-->\s*\n', text, re.S)
    if m:
        block = m.group(1)
        for line in block.splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue
            k, v = line.split(':', 1)
            metadata[k.strip()] = v.strip()
    # title: first H1
    title = None
    for line in text.splitlines():
        if line.startswith('# '):
            title = line.lstrip('# ').strip()
            break
    # summary: first paragraph after title
    summary = ''
    parts = re.split(r'\n\s*\n', text)
    for p in parts:
        p = p.strip()
        if p and not p.startswith('<!--') and not p.startswith('#'):
            summary = p.replace('\n', ' ').strip()
            break
    # topics: headings H2/H3
    topics = []
    for line in text.splitlines():
        if line.startswith('## '):
            topics.append(line.lstrip('# ').strip())
        elif line.startswith('### '):
            topics.append(line.lstrip('# ').strip())
    return metadata, title or os.path.basename(path), summary, topics

for path in sorted(md_files):
    rel = os.path.relpath(path, DOCS_DIR)
    parts = rel.split(os.sep)
    category = parts[0] if len(parts) > 1 else 'root'
    metadata, title, summary, topics = extract_metadata_and_content(path)
    last_updated = metadata.get('Last-updated')
    if not last_updated:
        ts = os.path.getmtime(path)
        last_updated = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
    id_slug = os.path.splitext(rel.replace(os.sep, '/'))[0].replace('/', '_')
    entry = {
        'id': id_slug,
        'category': category,
        'title': title,
        'file': rel.replace(os.sep, '/'),
        'source': {
            'path': rel.replace(os.sep, '/'),
            'github': f"{REPO_URL}/blob/main/docs/{rel.replace(os.sep, '/')}"
        },
        'summary': summary,
        'topics': topics,
        'last_updated': last_updated,
        'status': metadata.get('Status', 'canonical')
    }
    entries.append(entry)

index = {
    'version': '1.0.0',
    'platform': 'Clipstream TikTok-style Video Platform',
    'last_updated': datetime.utcnow().strftime('%Y-%m-%d'),
    'total_documents': len(entries),
    'categories': sorted(list({e['category'] for e in entries})),
    'documents': entries,
}

out_path = os.path.join(DOCS_DIR, 'RAG_INDEX.json')
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump(index, fh, indent=2, ensure_ascii=False)
print(f'Wrote {out_path} with {len(entries)} documents')
