#!/usr/bin/env python3
"""Import a pinned BioIcons source archive without executing upstream code."""
import argparse
import collections
import hashlib
import json
import shutil
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

COMMIT = 'd29e766ea7580b8063c4f47b29e872db40a4d979'
URLS = {
    'cc-0': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'cc-by-3.0': 'https://creativecommons.org/licenses/by/3.0/',
    'cc-by-4.0': 'https://creativecommons.org/licenses/by/4.0/',
    'cc-by-sa-3.0': 'https://creativecommons.org/licenses/by-sa/3.0/',
    'cc-by-sa-4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'mit': 'https://opensource.org/license/mit/',
    'bsd': 'https://opensource.org/license/bsd-3-clause/'
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive', type=Path)
    p.add_argument('--library', type=Path, default=Path(__file__).resolve().parents[1] / 'assets/library')
    args = p.parse_args()
    dest = args.library / 'bioicons'
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive, 'r:gz') as arc:
        for member in arc:
            rel = Path(*Path(member.name).parts[1:])
            if not member.isfile():
                continue
            if rel.parts[:2] == ('static', 'icons'):
                target = dest / Path(*rel.parts[1:])
            elif str(rel) in ('README.md', 'LICENSE', 'CITATION.cff'):
                target = dest / rel
            else:
                continue
            if not target.resolve().is_relative_to(dest.resolve()):
                raise ValueError('Unsafe archive path')
            target.parent.mkdir(parents=True, exist_ok=True)
            with arc.extractfile(member) as src, target.open('wb') as out:
                shutil.copyfileobj(src, out)
    data = json.loads((dest / 'icons/icons.json').read_text())
    authors = json.loads((dest / 'icons/authors.json').read_text())
    items, errors, unindexed = [], [], []
    author_lookup = {name.replace(' ', '_'): name for name in authors}
    # The checked-in web index can lag the files and normalizes author spaces.
    # Build from the actual SVG tree, keeping the web metadata as evidence.
    for path in sorted((dest / 'icons').rglob('*.svg')):
        rel = path.relative_to(dest / 'icons')
        if len(rel.parts) != 4:
            unindexed.append({'path': str(rel), 'reason': 'Author directory missing; provenance unresolved'})
            continue
        lic, category, author_dir, filename = rel.parts
        row = {'license': lic, 'category': category,
               'author': author_lookup.get(author_dir, author_dir), 'name': path.stem}
        raw = path.read_bytes()
        valid = True
        try:
            root = ET.fromstring(raw)
            if root.tag.split('}')[-1] != 'svg':
                raise ValueError('Not an SVG document')
        except (ET.ParseError, ValueError) as ex:
            valid = False
            errors.append({'path': str(rel), 'error': str(ex)})
        row = dict(row)
        row.update({
            'id': 'bio-' + hashlib.sha256(str(rel).encode()).hexdigest()[:12],
            'source': 'BioIcons', 'path': str(path.relative_to(args.library)),
            'author_url': authors.get(row['author'], ''),
            'license_url': URLS[row['license']],
            'license_path': 'bioicons/icons/' + row['license'] + '/LICENSE',
            'source_url': 'https://github.com/duerrsimon/bioicons/blob/' + COMMIT + '/static/icons/' + quote(str(rel)),
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'svg_valid': valid,
        })
        items.append(row)
    (args.library / 'index.json').write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n')
    report = {
        'source': 'https://github.com/duerrsimon/bioicons', 'commit': COMMIT,
        'download_date': '2026-10-30', 'assets': len(items), 'upstream_web_index_rows': len(data),
        'bytes': sum(x['bytes'] for x in items), 'licenses': dict(collections.Counter(x['license'] for x in items)),
        'categories': dict(collections.Counter(x['category'] for x in items)),
        'archive_sha256': hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        'svg_parse_errors': errors, 'unindexed_files': unindexed,
    }
    (args.library / 'snapshot.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
