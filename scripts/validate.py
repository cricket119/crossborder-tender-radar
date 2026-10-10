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
    assert urlparse(r['url']).scheme in ('http','https') and urlparse(r['url']).netloc
    assert r['targets'] and r['buyer'] and r['evidence']
    if r['deadline']: assert datetime.fromisoformat(r['deadline']).tzinfo
assert len({r['url'] for r in d['items']})==len(d['items']), 'Duplicate URL'
print(f"Validated {len(d['items'])} records, {len(d['leads'])} separate leads; all dates in {a}–{b}.")

registry=json.loads((p/'data/sources.json').read_text())
assert len({r['id'] for r in registry['sources']})==len(registry['sources'])
for r in registry['sources']:
    assert urlparse(r['url']).scheme in ('http','https')
    assert r['status'] in ('已读取','读取受限','待接入','需动态读取')
for r in d['items']:
    if r.get('registrationDeadline'): assert datetime.fromisoformat(r['registrationDeadline']).tzinfo
    if r['kind']=='采购结果': assert not r['deadline'], 'Result is not an open tender'
    for s in r.get('relatedSources',[]): assert urlparse(s['url']).scheme in ('http','https')
print(f"Validated {len(registry['sources'])} source channels and result/deadline distinctions.")
