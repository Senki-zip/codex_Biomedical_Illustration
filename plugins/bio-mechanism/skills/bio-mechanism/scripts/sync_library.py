#!/usr/bin/env python3
"""Refresh BioIcons or import the Reactome icon library with provenance."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import shutil
import sys
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from build_index import URLS

LIB = Path(__file__).resolve().parents[1] / 'assets/library'
TODAY = datetime.date.today().isoformat()
REACTOME_QUERY = 'https://reactome.org/ContentService/search/query'
try:
    import requests
except ImportError:
    requests = None
SESSIONS = threading.local()


def get(url):
    for attempt in range(3):
        try:
            if requests is not None:
                if not hasattr(SESSIONS, 'session'):
                    SESSIONS.session = requests.Session()
                    SESSIONS.session.headers['User-Agent'] = 'Biomedical-Illustration-Library/1.1'
                response = SESSIONS.session.get(url, timeout=35)
                response.raise_for_status()
                return response.content
            req = urllib.request.Request(url, headers={'User-Agent': 'Biomedical-Illustration-Library/1.1'})
            with urllib.request.urlopen(req, timeout=35) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_bytes(data)
    tmp.replace(path)


def save_json(path, data):
    save(path, (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode())


def inspect_svg(raw):
    try:
        root = ET.fromstring(raw)
        if root.tag.split('}')[-1] != 'svg':
            return False, 'Not an SVG document'
        return True, None
    except ET.ParseError as exc:
        return False, str(exc)


def merge(source, entries):
    index = LIB / 'index.json'
    previous = json.loads(index.read_text()) if index.exists() else []
    others = [x for x in previous if x['source'] != source]
    items = others + entries
    # Keep every ID addressable, while excluding byte-identical duplicates
    # from ordinary search. Prefer BioIcons so established IDs remain stable.
    items.sort(key=lambda x: (x['source'] != 'BioIcons', x['source'], x['id']))
    seen = {}
    for item in items:
        item.pop('duplicate_of', None)
        if item.get('svg_valid', True):
            if item['sha256'] in seen:
                item['duplicate_of'] = seen[item['sha256']]
            else:
                seen[item['sha256']] = item['id']
    save_json(index, items)
    save_json(LIB / 'catalogs' / (source.lower() + '.json'), entries)
    return {'indexed': len(entries), 'parseable': sum(x.get('svg_valid', True) for x in entries),
            'unique_usable_total': len(seen), 'duplicate_records': sum('duplicate_of' in x for x in items)}


def update_source(name, fields):
    path = LIB / 'sources.json'
    rows = json.loads(path.read_text()) if path.exists() else []
    row = next((x for x in rows if x['name'] == name), None)
    if row is None:
        row = {'name': name}
        rows.append(row)
    row.update(fields)
    save_json(path, rows)


def bioicons(workers):
    info = json.loads(get('https://api.github.com/repos/duerrsimon/bioicons/commits/main'))
    commit = info['sha']
    tree = json.loads(get('https://api.github.com/repos/duerrsimon/bioicons/git/trees/' + commit + '?recursive=1'))
    if tree.get('truncated'):
        raise ValueError('Incomplete GitHub tree; import not applied')
    raw_base = 'https://raw.githubusercontent.com/duerrsimon/bioicons/' + commit + '/'
    blobs = [x for x in tree['tree'] if x['type'] == 'blob' and
             (x['path'].startswith('static/icons/') or x['path'] in ('README.md', 'LICENSE', 'CITATION.cff'))]
    changed = []
    for blob in blobs:
        rel = Path(blob['path'])
        dest = LIB / 'bioicons' / (Path(*rel.parts[1:]) if rel.parts[0] == 'static' else rel)
        if dest.exists():
            data = dest.read_bytes()
            git_hash = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if git_hash == blob['sha']:
                continue
        changed.append((blob, dest))
    def download(pair):
        blob, dest = pair
        raw = get(raw_base + urllib.parse.quote(blob['path']))
        actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if actual != blob['sha']:
            raise ValueError('Upstream hash mismatch: ' + blob['path'])
        save(dest, raw)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(download, changed))
    authors = json.loads((LIB / 'bioicons/icons/authors.json').read_text())
    author_lookup = {k.replace(' ', '_'): k for k in authors}
    entries, skipped = [], []
    for blob in blobs:
        rel = Path(blob['path'])
        if not str(rel).endswith('.svg'):
            continue
        parts = rel.parts[2:]
        if len(parts) != 4:
            skipped.append({'path': str(rel), 'reason': 'Author directory missing'})
            continue
        license_id, category, author_dir, filename = parts
        if license_id not in URLS:
            raise ValueError('Unsupported upstream license: ' + license_id)
        path = LIB / 'bioicons/icons' / Path(*parts)
        raw = path.read_bytes()
        valid, error = inspect_svg(raw)
        author = author_lookup.get(author_dir, author_dir)
        entry = {'id': 'bio-' + hashlib.sha256(str(Path(*parts)).encode()).hexdigest()[:12],
                 'name': path.stem, 'category': category, 'author': author,
                 'source': 'BioIcons', 'path': str(path.relative_to(LIB)),
                 'author_url': authors.get(author, ''), 'license': license_id, 'license_url': URLS[license_id],
                 'license_path': 'bioicons/icons/' + license_id + '/LICENSE',
                 'source_url': 'https://github.com/duerrsimon/bioicons/blob/' + commit + '/' + urllib.parse.quote(blob['path']),
                 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'svg_valid': valid}
        if error:
            entry['svg_error'] = error
        entries.append(entry)
    report = {'source': 'BioIcons', 'checked_at': TODAY, 'commit': commit,
              'upstream_commit_date': info['commit']['committer']['date'],
              'checked_blobs': len(blobs), 'downloaded_files': len(changed), 'unindexed_files': skipped,
              **merge('BioIcons', entries)}
    update_source('BioIcons', {'status': 'downloaded', 'commit': commit, 'checked_at': TODAY,
                              'indexed_assets': len(entries), 'usable_svg': sum(x['svg_valid'] for x in entries),
                              'note': 'Latest main checked against per-file Git blob hashes; existing IDs and per-artwork licenses preserved.'})
    save_json(LIB / 'bioicons/update-report.json', report)
    return report


def reactome(workers, refresh):
    # The documented bulk archive can be unavailable; use the public icon
    # search catalog and the SVG links exposed by each icon's detail page.
    query = urllib.parse.urlencode({'query': '*', 'types': 'Icon', 'cluster': 'true', 'rows': 10000})
    data = json.loads(get(REACTOME_QUERY + '?' + query))
    expected = data['numberOfMatches']
    rows = [x for group in data['results'] for x in group['entries']]
    unique = {x['stId']: x for x in rows}
    if len(unique) != expected:
        raise ValueError('Reactome catalog did not return all unique icons; import not applied')
    dest = LIB / 'reactome'
    dest.mkdir(parents=True, exist_ok=True)
    save_json(dest / 'upstream-catalog.json', list(unique.values()))
    save(dest / 'LICENSE', (LIB / 'bioicons/icons/cc-by-4.0/LICENSE').read_bytes())
    notice = ('# Reactome Icon Library\n\n'
              'Artwork from Reactome, attributed to CSHL, OICR and EMBL-EBI.\n'
              'Individual designers and their URLs are recorded in the asset catalog.\n'
              'License: Creative Commons Attribution 4.0 International (CC BY 4.0).\n'
              'Source and license declaration: https://reactome.org/icon-lib\n'
              'License URL: https://creativecommons.org/licenses/by/4.0/\n')
    save(dest / 'NOTICE.md', notice.encode())
    def download(row):
        stid = row['stId']
        if not stid.startswith('R-ICO-') or not stid[6:].isdigit():
            raise ValueError('Unexpected Reactome icon identifier')
        path = dest / 'icons' / (stid + '.svg')
        try:
            if refresh or not path.exists():
                raw = get('https://reactome.org/icon/' + stid + '.svg')
                valid, error = inspect_svg(raw)
                if not valid:
                    raise ValueError('Invalid SVG: ' + str(error))
                save(path, raw)
            raw = path.read_bytes()
            valid, error = inspect_svg(raw)
            return {'id': 'reactome-' + stid, 'name': row.get('iconName', row['name']),
                    'category': ' / '.join(row.get('iconCategories', ['uncategorized'])),
                    'author': row.get('iconDesignerName', 'Reactome'),
                    'author_url': row.get('iconDesignerUrl', 'https://reactome.org/'),
                    'publisher': 'Reactome (CSHL, OICR, EMBL-EBI)',
                    'source': 'Reactome', 'source_id': stid, 'path': str(path.relative_to(LIB)),
                    'license': 'cc-by-4.0', 'license_url': URLS['cc-by-4.0'],
                    'license_path': 'reactome/LICENSE', 'notice_paths': ['reactome/NOTICE.md'],
                    'source_url': 'https://reactome.org/content/detail/' + stid,
                    'download_url': 'https://reactome.org/icon/' + stid + '.svg',
                    'description': row.get('summation', ''), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'bytes': len(raw), 'svg_valid': valid, 'retrieved_at': TODAY}, None
        except Exception as exc:
            return None, {'id': stid, 'error': str(exc)}
    entries, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for n, (entry, failure) in enumerate(pool.map(download, unique.values()), 1):
            if entry:
                entries.append(entry)
            if failure:
                failures.append(failure)
            if n % 100 == 0 or n == len(unique):
                print('Reactome: %d/%d processed, %d failed' % (n, len(unique), len(failures)), file=sys.stderr, flush=True)
    entries.sort(key=lambda x: x['id'])
    report = {'source': 'Reactome', 'checked_at': TODAY, 'expected': expected,
              'download_failures': failures, **merge('Reactome', entries)}
    update_source('Reactome Icon Library', {'status': 'downloaded' if not failures else 'partially_downloaded',
                  'website': 'https://reactome.org/icon-lib', 'bulk_download_status': 'public icon API used',
                  'checked_at': TODAY, 'indexed_assets': len(entries), 'expected_assets': expected,
                  'download_failures': len(failures), 'note': 'Individual SVGs downloaded with original designer metadata; CC BY 4.0 and Reactome attribution preserved.'})
    save_json(dest / 'update-report.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', choices=['bioicons', 'reactome'])
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--refresh', action='store_true', help='Re-fetch existing Reactome SVGs')
    args = p.parse_args()
    if not 1 <= args.workers <= 8:
        p.error('--workers must be 1..8')
    report = bioicons(args.workers) if args.source == 'bioicons' else reactome(args.workers, args.refresh)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(report.get('download_failures')))


if __name__ == '__main__':
    sys.exit(main())
