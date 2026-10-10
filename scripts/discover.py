"""Discover candidate links, never auto-publish notices.

Standard library only. Robots-aware, one listing request per source by default.
Use --input with TinyFish HTML fetch results for dynamic pages. Extracted Markdown
is not accepted as HTML. Candidate dates are hints, never announcement dates.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
AGENT = 'CrossborderTenderRadar/1.0'
MAX_BYTES = 4 * 1024 * 1024

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            a = dict(attrs)
            self.current = [a.get('href', ''), a.get('title', '')]
    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(tuple(self.current))
            self.current = None

def candidates(html, base, source, words):
    parser = Links()
    parser.feed(html)
    output = []
    seen = set()
    for href, title in parser.links:
        title = re.sub(r'\s+', ' ', title).strip()
        url = urldefrag(urljoin(base, href))[0]
        if urlparse(url).scheme not in ('http', 'https') or url in seen:
            continue
        hit = {g: [w for w in ws if w.casefold() in title.casefold()] for g, ws in words.items()}
        if not all(hit[g] for g in ('crossborder', 'service', 'procurement')) or hit['exclude']:
            continue
        seen.add(url)
        output.append(dict(id=hashlib.sha256(url.encode()).hexdigest()[:16],
            title=title, url=url, sourceId=source, foundOn=base, keywordMatches=hit,
            verification='pending', published=None))
    return output

def request(url):
    with urlopen(Request(url, headers={'User-Agent': AGENT}), timeout=15) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Page exceeds size limit')
        if 'html' not in response.headers.get_content_type():
            raise ValueError('Listing is not HTML; use a PDF reader or source adapter')
        encoding = response.headers.get_content_charset()
        if not encoding:
            match = re.search(br'charset=["\x27]?([A-Za-z0-9_-]+)', raw[:4096], re.I)
            encoding = match.group(1).decode('ascii') if match else 'utf-8'
        return raw.decode(encoding, errors='replace'), response.url

def allowed(url):
    origin = '{0.scheme}://{0.netloc}'.format(urlparse(url))
    robots = RobotFileParser(origin + '/robots.txt')
    try:
        with urlopen(Request(robots.url, headers={'User-Agent': AGENT}), timeout=10) as response:
            robots.parse(response.read(256000).decode('utf-8', errors='replace').splitlines())
    except Exception as e:
        # 404 means no published robots file; other failures are not permission.
        if getattr(e, 'code', None) == 404:
            return True, 2
        return False, 'robots_unavailable: ' + type(e).__name__
    return robots.can_fetch(AGENT, url), max(2, robots.crawl_delay(AGENT) or 0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', action='append', help='Source IDs, repeatable')
    parser.add_argument('--input', type=Path, help='TinyFish HTML fetch JSON')
    parser.add_argument('--plan', action='store_true', help='Print search matrix without fetching')
    parser.add_argument('--output', type=Path, default=ROOT/'output/discovery.json')
    args = parser.parse_args()
    registry = json.loads((ROOT/'data/sources.json').read_text(encoding='utf-8'))
    sources = [s for s in registry['sources'] if not args.source or s['id'] in args.source]
    if args.plan:
        print(json.dumps([dict(source=s['id'], query='site:'+urlparse(s['url']).hostname+' '+q)
            for s in sources for q in registry['queryFamilies']], ensure_ascii=False, indent=2))
        return
    report = dict(startedAt=datetime.now(timezone.utc).isoformat(), sources=[], candidates=[])
    if args.input:
        payload = json.loads(args.input.read_text(encoding='utf-8'))
        for row in payload.get('results', []):
            host = urlparse(row['url']).hostname
            src = next((s['id'] for s in sources if urlparse(s['url']).hostname == host), 'unregistered')
            if row.get('format') != 'html':
                report['sources'].append(dict(id=src, url=row['url'], status='skipped_non_html'))
                continue
            matches = candidates(row.get('text', ''), row.get('final_url') or row['url'], src, registry['keywords'])
            report['candidates'].extend(matches)
            report['sources'].append(dict(id=src, url=row['url'], status='imported_html', count=len(matches)))
        report['errors'] = payload.get('errors', [])
    else:
        for s in sources:
            if not s.get('crawl'):
                continue
            try:
                ok, delay = allowed(s['url'])
                if not ok:
                    report['sources'].append(dict(id=s['id'], status='robots_skipped', reason=str(delay)))
                    continue
                time.sleep(delay)
                html, final = request(s['url'])
                matches = candidates(html, final, s['id'], registry['keywords'])
                report['candidates'].extend(matches)
                report['sources'].append(dict(id=s['id'], status='read', count=len(matches)))
            except Exception as e:
                report['sources'].append(dict(id=s['id'], status='failed', reason=type(e).__name__))
    report['candidates'] = list({c['url']: c for c in report['candidates']}.values())
    report['finishedAt'] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Candidate links:', len(report['candidates']), '; report:', args.output)

if __name__ == '__main__':
    main()
