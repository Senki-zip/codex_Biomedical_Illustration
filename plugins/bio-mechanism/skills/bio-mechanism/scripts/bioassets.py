#!/usr/bin/env python3
"""Offline asset search, BioRender import bundles, and editable SVG composition."""
import argparse
import base64
import collections
import hashlib
import html
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
LIB = SKILL / 'assets/library'
SVG = 'http://www.w3.org/2000/svg'
XLINK = 'http://www.w3.org/1999/xlink'
ET.register_namespace('', SVG)
ET.register_namespace('xlink', XLINK)
ALIASES = {
    '细胞核': ['nucleus', 'nuclei'], '核仁': ['nucleolus'], '染色质': ['chromatin', 'nucleosome'],
    '染色体': ['chromosome'], '核小体': ['nucleosome'], '组蛋白': ['histone'],
    '转录因子': ['transcription', 'factor'], '转录': ['transcription', 'rna'],
    '增强子': ['enhancer', 'dna', 'chromatin'], '启动子': ['promoter', 'dna'],
    '核酸': ['nucleic', 'dna', 'rna'], '基因': ['gene', 'genetics', 'dna'],
    '信使RNA': ['mrna'], '信使rna': ['mrna'], '蛋白质': ['protein'], '蛋白': ['protein'],
    '受体': ['receptor'], '配体': ['ligand'], '细胞膜': ['membrane'],
    '细胞器': ['intracellular'], '细胞': ['cell'], '线粒体': ['mitochondria', 'mitochondrion'],
    '内质网': ['reticulum'], '高尔基体': ['golgi'], '溶酶体': ['lysosome'],
    '核糖体': ['ribosome'], '细胞骨架': ['cytoskeleton', 'actin', 'microtubule'],
    '免疫': ['immunology', 'immune'], '巨噬细胞': ['macrophage'], '树突细胞': ['dendritic'],
    '红细胞': ['erythrocyte', 'red blood'], '血小板': ['platelet'], '中性粒细胞': ['neutrophil'],
    '抗体': ['antibody', 'immunoglobulin'], '抗原': ['antigen'], '白细胞': ['leukocyte'],
    'T细胞': ['t cell', 'lymphocyte'], 'B细胞': ['b cell', 'lymphocyte'],
    '病毒': ['virus', 'viral'], '细菌': ['bacteria', 'bacterium'], '肿瘤': ['tumor', 'cancer'],
    '凋亡': ['apoptosis'], '自噬': ['autophagy'], '囊泡': ['vesicle'], '外泌体': ['exosome', 'vesicle'],
    '小鼠': ['mouse', 'mice'], '动物': ['animals'], '组织': ['tissue'],
    '培养皿': ['petri', 'culture'], '移液器': ['pipette'], '试管': ['tube'],
    '测序': ['sequencing'], '显微镜': ['microscope'], '实验': ['lab', 'apparatus'],
    '磷酸化': ['phosphorylation'], '激酶': ['kinase'], '信号通路': ['signaling', 'receptor'],
}


def load_index():
    if not (LIB / 'index.json').exists():
        raise ValueError('Library is missing. Import a source archive with scripts/build_index.py first.')
    return json.loads((LIB / 'index.json').read_text())


def norm(s):
    return re.sub(r'[_\-]+', ' ', s).casefold()


def find(query, items, limit=20, category=None, license=None, author=None):
    # Alias groups are alternatives. Separate user concepts contribute separate scores.
    remaining, groups = query, []
    for zh in sorted(ALIASES, key=len, reverse=True):
        if zh in remaining:
            groups.append([norm(x) for x in ALIASES[zh]])
            remaining = remaining.replace(zh, ' ')
    groups.extend([norm(x)] for x in re.findall(r'[\w]+', remaining) if x.strip())
    ranked = []
    for item in items:
        if not item.get('svg_valid', True):
            continue
        if category and norm(category) not in norm(item['category']):
            continue
        if license and item['license'] != license:
            continue
        if author and norm(author) not in norm(item['author']):
            continue
        name = norm(item['name'])
        hay = norm(' '.join(str(item[k]) for k in ('name', 'category', 'author')))
        hits = sum(any(term in hay for term in group) for group in groups)
        if groups and not hits:
            continue
        score = 10 * hits + sum(any(term in name for term in group) for group in groups)
        if norm(query) == name:
            score += 100
        ranked.append((score, item))
    ranked.sort(key=lambda v: (-v[0], v[1]['bytes'], v[1]['name'].casefold()))
    return [x[1] for x in (ranked[:limit] if limit > 0 else ranked)]


def asset_path(item):
    p = (LIB / item['path']).resolve()
    if not p.is_relative_to(LIB.resolve()):
        raise ValueError('Asset path outside library')
    return p


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def attribution(items, out, modification='Original artwork copied without changes.'):
    out.mkdir(parents=True, exist_ok=True)
    lines = ['# Artwork attribution', '', modification, '',
             'Each artwork retains its own license. These are open-source library assets, not BioRender proprietary icons.', '']
    for item in items:
        lines.extend([
            f"- **{item['name']}** — {item['author']} ({item.get('author_url', '')}); "
            f"[{item['license']}]({item['license_url']}); [source]({item['source_url']}). ID: `{item['id']}`.",
        ])
        license_src = LIB / item['license_path']
        license_dst = out / 'licenses' / (item['license'] + '.txt')
        license_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(license_src, license_dst)
    (out / 'ATTRIBUTION.md').write_text('\n'.join(lines) + '\n')
    write_json(out / 'assets.json', items)


def gallery(items, out):
    cards = []
    for item in items:
        uri = 'data:image/svg+xml;base64,' + base64.b64encode(asset_path(item).read_bytes()).decode()
        cards.append(f'<article><img src="{uri}" alt="{html.escape(item["name"], quote=True)}"><h3>{html.escape(item["name"])}</h3>'
                     f'<code>{item["id"]}</code><p>{html.escape(item["category"])} · {html.escape(item["author"])}</p>'
                     f'<a href="{html.escape(item["source_url"], quote=True)}">来源</a> · '
                     f'<a href="{item["license_url"]}">{item["license"]}</a></article>')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>科研素材预览</title>'
                   '<style>body{font:15px system-ui;background:#f5f7fa;color:#203246;margin:32px}'
                   'main{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:20px}'
                   'article{background:white;border:1px solid #dce4ed;padding:18px;border-radius:12px;overflow-wrap:anywhere}'
                   'img{width:100%;height:175px;object-fit:contain}h3{font-size:16px}p{font-size:12px;color:#53657a}'
                   'code{font-size:12px}a{color:#126c98}</style><h1>科研机制图素材库</h1>'
                   f'<p>{len(items)} 个候选素材 · 原始 SVG · 作者与许可随条目显示</p><main>' + ''.join(cards) + '</main></html>')


def elem(tag, attrs=None, text=None):
    e = ET.Element('{' + SVG + '}' + tag, {str(k): str(v) for k, v in (attrs or {}).items()})
    e.text = text
    return e


def safe_embed(item, node, prefix):
    raw = asset_path(item).read_bytes()
    if b'<!ENTITY' in raw.upper():
        raise ValueError('Entity declarations are not supported in embedded artwork')
    root = ET.fromstring(raw)
    # Source artwork is data: remove active nodes and prevent remote file requests.
    for parent in root.iter():
        for child in list(parent):
            if child.tag.split('}')[-1].lower() in ('script', 'foreignobject'):
                parent.remove(child)
        for key, val in list(parent.attrib.items()):
            if key.split('}')[-1].lower().startswith('on'):
                del parent.attrib[key]
            elif key.split('}')[-1] in ('href', 'src') and not val.startswith(('#', 'data:')):
                raise ValueError('External resource reference in artwork: ' + item['id'])
        if parent.tag.split('}')[-1] == 'style' and parent.text:
            if re.search(r'@import|url\(\s*[\'"]?(?:https?:|file:|//)', parent.text, re.I):
                raise ValueError('External CSS reference in artwork')
    ids = {e.attrib['id']: prefix + e.attrib['id'] for e in root.iter() if 'id' in e.attrib}
    classes = {c: prefix + c for e in root.iter() for c in e.attrib.get('class', '').split()}
    def replace_refs(value):
        for old, new in ids.items():
            value = re.sub(r'(?<=#)' + re.escape(old) + r'(?![\w.-])', new, value)
        return value
    for e in root.iter():
        for k, v in list(e.attrib.items()):
            if k == 'id':
                e.attrib[k] = ids[v]
            elif k == 'class':
                e.attrib[k] = ' '.join(classes[c] for c in v.split())
            else:
                e.attrib[k] = replace_refs(v)
        if e.tag.split('}')[-1] == 'style' and e.text:
            e.text = replace_refs(e.text)
            for old, new in classes.items():
                e.text = re.sub(r'(?<=\.)' + re.escape(old) + r'(?![\w-])', new, e.text)
    if 'viewBox' not in root.attrib:
        w = re.match(r'[\d.]+', root.attrib.get('width', '100'))
        h = re.match(r'[\d.]+', root.attrib.get('height', '100'))
        root.set('viewBox', '0 0 ' + (w.group() if w else '100') + ' ' + (h.group() if h else '100'))
    for k in ('x', 'y', 'width', 'height'):
        root.set(k, str(node[k]))
    root.set('preserveAspectRatio', 'xMidYMid meet')
    return root


def anchor(n, side):
    x, y, w, h = [float(n[k]) for k in ('x', 'y', 'width', 'height')]
    return {'left': (x, y+h/2), 'right': (x+w, y+h/2), 'top': (x+w/2, y),
            'bottom': (x+w/2, y+h), 'center': (x+w/2, y+h/2)}[side]


def add_node(canvas, n, lookup, used, i):
    group = elem('g', {'id': 'node-' + n['id']})
    if n.get('asset'):
        if n['asset'] not in lookup:
            raise ValueError('Unknown asset: ' + n['asset'])
        item = lookup[n['asset']]
        group.append(safe_embed(item, n, 'asset' + str(i) + '-'))
        used[item['id']] = item
    else:
        attrs = {'fill': n.get('fill', '#eef4f8'), 'stroke': n.get('stroke', '#9caebe'), 'stroke-width': n.get('stroke_width', 1.5)}
        if n.get('shape') == 'ellipse':
            attrs.update(cx=n['x']+n['width']/2, cy=n['y']+n['height']/2, rx=n['width']/2, ry=n['height']/2)
            group.append(elem('ellipse', attrs))
        else:
            attrs.update({k: n[k] for k in ('x', 'y', 'width', 'height')})
            attrs['rx'] = n.get('radius', 12)
            group.append(elem('rect', attrs))
    label_y = (n['y'] + n['height']/2 + 6 if n.get('label_position') == 'inside'
               else n['y'] + n['height'] + n.get('label_offset', 27))
    if n.get('label'):
        group.append(elem('text', {'x': n['x']+n['width']/2, 'y': label_y, 'text-anchor': 'middle',
                                  'font-size': n.get('label_size', 21), 'fill': n.get('label_color', '#203246')}, n['label']))
    if n.get('note'):
        group.append(elem('text', {'x': n['x']+n['width']/2, 'y': label_y+24, 'text-anchor': 'middle',
                                  'font-size': 14, 'fill': '#64748b'}, n['note']))
    canvas.append(group)


def compose(spec_path, out, items):
    spec = json.loads(spec_path.read_text())
    nodes = spec.get('nodes', [])
    lookup = {x['id']: x for x in items if x.get('svg_valid', True)}
    node_map = {}
    for n in nodes:
        if n['id'] in node_map:
            raise ValueError('Duplicate node ID: ' + n['id'])
        for k in ('x', 'y', 'width', 'height'):
            if not isinstance(n.get(k), (int, float)) or not math.isfinite(n[k]):
                raise ValueError('Node requires finite x/y/width/height')
        if n['width'] <= 0 or n['height'] <= 0:
            raise ValueError('Node dimensions must be positive')
        node_map[n['id']] = n
    w, h = spec.get('width', 1200), spec.get('height', 700)
    root = elem('svg', {'width': w, 'height': h, 'viewBox': f'0 0 {w} {h}',
                       'font-family': 'Arial, Noto Sans CJK SC, PingFang SC, sans-serif'})
    root.append(elem('title', text=spec.get('title', 'Biological mechanism diagram')))
    root.append(elem('rect', {'width': w, 'height': h, 'fill': spec.get('background', '#ffffff')}))
    defs = elem('defs')
    root.append(defs)
    used = {}
    for i, n in enumerate(nodes):
        if n.get('panel'):
            add_node(root, n, lookup, used, i)
    for i, e in enumerate(spec.get('edges', [])):
        a, b = node_map[e['from']], node_map[e['to']]
        horizontal = abs(b['x']-a['x']) >= abs(b['y']-a['y'])
        sa, sb = (('right', 'left') if b['x'] >= a['x'] else ('left', 'right')) if horizontal else (
            ('bottom', 'top') if b['y'] >= a['y'] else ('top', 'bottom'))
        points = e.get('points') or [anchor(a, e.get('from_anchor', sa)), anchor(b, e.get('to_anchor', sb))]
        color, kind = e.get('color', '#375a72'), e.get('kind', 'activation')
        if kind not in ('activation', 'inhibition', 'binding'):
            raise ValueError('Unknown edge kind: ' + kind)
        marker_id = 'edge-tip-' + str(i)
        if kind != 'binding':
            marker = elem('marker', {'id': marker_id, 'markerWidth': 12, 'markerHeight': 12,
                                    'refX': 10, 'refY': 6, 'orient': 'auto', 'markerUnits': 'userSpaceOnUse'})
            marker.append(elem('path', {'d': 'M1,1 L10,6 L1,11 Z' if kind == 'activation' else 'M10,0 L10,12',
                                        'fill': color if kind == 'activation' else 'none', 'stroke': color, 'stroke-width': 2.5}))
            defs.append(marker)
        attrs = {'points': ' '.join(f'{x},{y}' for x, y in points), 'fill': 'none', 'stroke': color,
                 'stroke-width': e.get('width', 3), 'stroke-linejoin': 'round'}
        if kind != 'binding':
            attrs['marker-end'] = 'url(#' + marker_id + ')'
        if e.get('dashed'):
            attrs['stroke-dasharray'] = '8 6'
        root.append(elem('polyline', attrs))
        if e.get('label'):
            mid_a, mid_b = points[(len(points)-1)//2], points[len(points)//2]
            root.append(elem('text', {'x': e.get('label_x', (mid_a[0]+mid_b[0])/2),
                                      'y': e.get('label_y', (mid_a[1]+mid_b[1])/2-14),
                                      'font-size': e.get('label_size', 16), 'text-anchor': 'middle', 'fill': color}, e['label']))
    for i, n in enumerate(nodes):
        if not n.get('panel'):
            add_node(root, n, lookup, used, i)
    if spec.get('title'):
        root.append(elem('text', {'x': 32, 'y': 43, 'font-size': 26, 'font-weight': 600, 'fill': '#183449'}, spec['title']))
    for label in spec.get('labels', []):
        root.append(elem('text', {'x': label['x'], 'y': label['y'], 'font-size': label.get('size', 18),
                                  'fill': label.get('color', '#334155'), 'font-weight': label.get('weight', 400),
                                  'text-anchor': label.get('anchor', 'start')}, label['text']))
    root.append(elem('metadata', text=json.dumps({'assets': list(used.values()), 'scene': spec}, ensure_ascii=False)))
    out.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(out, encoding='utf-8', xml_declaration=True)
    write_json(out.with_suffix('.scene.json'), spec)
    attribution(list(used.values()), out.with_name(out.stem + '-sources'),
                'Artwork scaled and placed in a composite diagram. Source paths and colors preserved; active content removed if present. Labels and connectors added separately.')
    print(str(out.resolve()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('stats'); s.add_argument('--verify', action='store_true')
    s = sub.add_parser('search'); s.add_argument('query', nargs='?', default='')
    s.add_argument('--limit', type=int, default=20); s.add_argument('--category'); s.add_argument('--license'); s.add_argument('--author')
    s.add_argument('--json', action='store_true'); s.add_argument('--gallery', type=Path)
    s = sub.add_parser('export'); s.add_argument('ids', nargs='+'); s.add_argument('--out', required=True, type=Path)
    s = sub.add_parser('compose'); s.add_argument('--spec', required=True, type=Path); s.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    items = load_index()
    if args.command == 'stats':
        result = {'assets': len(items), 'svg_bytes': sum(x['bytes'] for x in items),
                  'licenses': dict(collections.Counter(x['license'] for x in items)),
                  'categories': dict(collections.Counter(x['category'] for x in items)),
                  'sources': json.loads((LIB / 'sources.json').read_text()) if (LIB / 'sources.json').exists() else []}
        if args.verify:
            errors = []
            quarantined = [x['id'] for x in items if not x.get('svg_valid', True)]
            for item in items:
                try:
                    raw = asset_path(item).read_bytes()
                    if hashlib.sha256(raw).hexdigest() != item['sha256']:
                        raise ValueError('SHA-256 mismatch')
                    if item.get('svg_valid', True):
                        ET.fromstring(raw)
                except (OSError, ValueError, ET.ParseError) as ex:
                    errors.append({'id': item['id'], 'error': str(ex)})
            result['verification_errors'] = errors
            result['verified'] = len(items) - len(errors)
            result['usable_svg'] = len(items) - len(quarantined)
            result['quarantined_upstream_svg'] = quarantined
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return int(bool(errors))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'search':
        matches = find(args.query, items, args.limit, args.category, args.license, args.author)
        if args.gallery:
            gallery(matches, args.gallery)
        if args.json:
            print(json.dumps(matches, ensure_ascii=False, indent=2))
        else:
            for x in matches:
                print(f"{x['id']}\t{x['name']}\t{x['category']}\t{x['author']}\t{x['license']}")
            print(f'{len(matches)} result(s)', file=sys.stderr)
    elif args.command == 'export':
        lookup = {x['id']: x for x in items if x.get('svg_valid', True)}
        unknown = set(args.ids) - set(lookup)
        if unknown:
            raise ValueError('Unknown asset IDs: ' + ', '.join(sorted(unknown)))
        selected = [lookup[i] for i in dict.fromkeys(args.ids)]
        args.out.mkdir(parents=True, exist_ok=True)
        for x in selected:
            filename = x['id'] + '-' + re.sub(r'[^\w.-]+', '_', x['name']) + '.svg'
            shutil.copyfile(asset_path(x), args.out / filename)
        attribution(selected, args.out)
        print(f'Exported {len(selected)} SVGs to {args.out.resolve()}')
    else:
        compose(args.spec, args.out, items)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, ET.ParseError) as ex:
        print('Error: ' + str(ex), file=sys.stderr)
        sys.exit(1)
