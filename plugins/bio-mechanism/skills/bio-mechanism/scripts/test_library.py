"""Behavior checks for merging and exporting multiple artwork sources."""
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

import bioassets
import sync_library


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lib = Path(self.tmp.name)
        self.old_lib, self.old_sync_lib = bioassets.LIB, sync_library.LIB
        bioassets.LIB = sync_library.LIB = self.lib

    def tearDown(self):
        bioassets.LIB, sync_library.LIB = self.old_lib, self.old_sync_lib
        self.tmp.cleanup()

    def item(self, name, source, raw=None, license_text='license notice'):
        raw = raw or ('<svg xmlns="http://www.w3.org/2000/svg"><title>' + name + '</title></svg>').encode()
        folder = self.lib / source
        folder.mkdir(exist_ok=True)
        (folder / (name + '.svg')).write_bytes(raw)
        (folder / 'LICENSE').write_text(license_text)
        return {'id': name, 'source': source, 'name': name, 'author': 'Original Designer',
                'category': 'receptor', 'description': 'signal protein', 'author_url': 'https://example.org/designer',
                'path': source + '/' + name + '.svg', 'license': 'cc-by-4.0',
                'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                'license_path': source + '/LICENSE', 'source_url': 'https://example.org/' + name,
                'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'svg_valid': True}

    def test_merge_preserves_other_sources_ids_and_deduplicates(self):
        a = self.item('existing-id', 'BioIcons')
        sync_library.merge('BioIcons', [a])
        b = self.item('alias-id', 'Reactome', (self.lib / a['path']).read_bytes())
        c = self.item('new-id', 'Reactome')
        sync_library.merge('Reactome', [b, c])
        sync_library.merge('BioIcons', [a])
        index = bioassets.load_index()
        self.assertEqual({x['id'] for x in index}, {'existing-id', 'alias-id', 'new-id'})
        alias = next(x for x in index if x['id'] == 'alias-id')
        self.assertEqual(alias['duplicate_of'], 'existing-id')
        matches = bioassets.find('protein', index, source='Reactome')
        self.assertEqual([x['id'] for x in matches], ['new-id'])

    def test_mixed_source_export_keeps_distinct_license_notices(self):
        a = self.item('a', 'BioIcons', license_text='original author notice A')
        b = self.item('b', 'Reactome', license_text='original author notice B')
        notice = self.lib / 'Reactome/NOTICE.md'
        notice.write_text('Reactome: CSHL, OICR, EMBL-EBI')
        b.update(publisher='Reactome (CSHL, OICR, EMBL-EBI)', notice_paths=['Reactome/NOTICE.md'])
        out = self.lib / 'export'
        bioassets.attribution([a, b], out)
        texts = [p.read_text() for p in (out / 'licenses').iterdir()]
        self.assertIn('original author notice A', texts)
        self.assertIn('original author notice B', texts)
        self.assertIn(notice.read_text(), texts)
        self.assertIn('CSHL, OICR, EMBL-EBI', (out / 'ATTRIBUTION.md').read_text())
        self.assertEqual(len(json.loads((out / 'assets.json').read_text())), 2)

    def test_standard_svg_entities_are_composable(self):
        raw = b'<!DOCTYPE svg [<!ENTITY paint "#123456">]><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><path fill="&paint;" d="M0 0h10v10z"/></svg>'
        item = self.item('entity', 'BioIcons', raw)
        self.assertTrue(sync_library.inspect_svg(raw)[0])
        embedded = bioassets.safe_embed(item, {'x': 0, 'y': 0, 'width': 10, 'height': 10}, 'test-')
        self.assertEqual(list(embedded)[0].get('fill'), '#123456')

    def test_invalid_source_documents_are_rejected(self):
        self.assertFalse(sync_library.inspect_svg(b'')[0])
        self.assertFalse(sync_library.inspect_svg(b'<html/>')[0])
        self.assertFalse(sync_library.inspect_svg(b'<svg>')[0])

    def test_archive_import_does_not_erase_reactome(self):
        other = self.item('retained', 'Reactome')
        sync_library.merge('Reactome', [other])
        raw = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
        files = {'static/icons/cc-0/Genetics/Artist/new.svg': raw,
                 'static/icons/icons.json': b'[]', 'static/icons/authors.json': b'{}',
                 'static/icons/cc-0/LICENSE': b'CC0'}
        archive = self.lib / 'source.tgz'
        with tarfile.open(archive, 'w:gz') as tar:
            for name, data in files.items():
                member = tarfile.TarInfo('bioicons-snapshot/' + name)
                member.size = len(data)
                tar.addfile(member, io.BytesIO(data))
        script = Path(__file__).with_name('build_index.py')
        subprocess.run([sys.executable, str(script), str(archive), '--library', str(self.lib)],
                       check=True, capture_output=True)
        items = bioassets.load_index()
        self.assertEqual({x['source'] for x in items}, {'BioIcons', 'Reactome'})
        self.assertIn('retained', {x['id'] for x in items})


if __name__ == '__main__':
    unittest.main()
