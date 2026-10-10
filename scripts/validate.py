"""Validate evidence-backed data before publishing. No network access needed."""
import json
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
p=Path(__file__).resolve().parents[1]
d=json.loads((p/'data/tenders.json').read_text())
a=date.fromisoformat(d['meta']['windowStart']);b=date.fromisoformat(d['meta']['windowEnd'])
seen=set()
for r in d['items']:
    assert r['id'] not in seen, 'Duplicate ID';seen.add(r['id'])
    assert a<=date.fromisoformat(r['published'])<=b, 'Outside observation window'
    assert urlparse(r['url']).scheme=='https' and urlparse(r['url']).netloc
    assert r['targets'] and r['buyer'] and r['evidence']
    if r['deadline']: assert datetime.fromisoformat(r['deadline']).tzinfo
assert len({r['url'] for r in d['items']})==len(d['items']), 'Duplicate URL'
print(f"Validated {len(d['items'])} records, {len(d['leads'])} separate leads; all dates in {a}–{b}.")
