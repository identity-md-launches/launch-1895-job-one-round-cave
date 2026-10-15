#!/usr/bin/env python3
"""Check round 29 record/image/gallery structure offline, not visual fidelity."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import zlib


class Gallery(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.records, self.images, self.links, self.tags = [], [], [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if 'data-record' in attrs:
            self.records.append(attrs['data-record'])
        if tag == 'img':
            self.images.append(attrs['src'])
        if tag == 'a':
            self.links.append(attrs['href'])
        assert not any(key.lower().startswith('on') for key in attrs)


def png_dimensions(raw):
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    offset, dimensions, ended = 8, None, False
    while offset < len(raw):
        length = struct.unpack('>I', raw[offset:offset+4])[0]
        kind = raw[offset+4:offset+8]
        data = raw[offset+8:offset+8+length]
        crc = struct.unpack('>I', raw[offset+8+length:offset+12+length])[0]
        assert zlib.crc32(kind + data) == crc
        if kind == b'IHDR':
            dimensions = struct.unpack('>II', data[:8])
        offset += length + 12
        if kind == b'IEND':
            ended = True
            break
    assert ended and offset == len(raw)
    return dimensions


def jpeg_dimensions(raw):
    assert raw[:2] == b'\xff\xd8' and raw[-2:] == b'\xff\xd9'
    offset = 2
    while offset < len(raw):
        assert raw[offset] == 255
        kind = raw[offset + 1]
        length = int.from_bytes(raw[offset+2:offset+4], 'big')
        if kind in (0xc0, 0xc1, 0xc2):
            height, width = struct.unpack('>HH', raw[offset+5:offset+9])
            return width, height
        offset += length + 2
    raise AssertionError('JPEG has no frame dimensions')


def main():
    wall = Path('artifacts/gathering/wall-v9.png').read_bytes()
    assert wall == Path('artifacts/gathering/wall.png').read_bytes()
    assert png_dimensions(wall) == (1254, 1254)
    jpeg = Path('dist/gathering/29.jpg').read_bytes()
    assert jpeg_dimensions(jpeg) == (512, 512)
    assert len(jpeg) < 100000
    digest = hashlib.sha256(wall).hexdigest()
    record = json.loads(Path('dist/gathering/29.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
    attrs = {a['trait_type']: a['value'] for a in record['attributes']}
    assert len(attrs) == len(record['attributes']) == 6
    assert set(attrs) == {'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing'}
    assert attrs['Cave'] == 'Ice' and attrs['Wall'] == 'Gathering'
    assert type(attrs['Number']) is int and attrs['Number'] == 29
    assert attrs['One thing'] == 'Gathering'
    assert json.loads(Path('dist/goals.json').read_text()) == [
        {'line': n, 'goal': Path(f'line-{n}/GOAL.md').read_text().strip()} for n in range(1, 5)]
    sources = sorted(Path('dist').glob('*/[0-9][0-9].json'))
    expected = {p.relative_to('dist').as_posix() for p in sources}
    content = Path('dist/index.html').read_text()
    gallery = Gallery(content)
    assert len(content.encode()) < 100000
    assert len(gallery.records) == len(expected) == 145
    assert set(gallery.records) == expected
    assert len(gallery.images) == 45
    assert all(re.fullmatch(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', src) for src in gallery.images)
    assert not set(gallery.tags) & {'script', 'iframe', 'link'}
    for href in gallery.links:
        if href.startswith('#'):
            assert f'id="{href[1:]}"' in content
        elif not href.startswith('https://'):
            assert (Path('dist') / href).is_file(), href
    for wall_name in ('gathering', 'line-1', 'line-2', 'line-3', 'line-4'):
        keys = [key for key in gallery.records if key.startswith(wall_name + '/')]
        for unpainted in (False, True):
            subset = [key for key in keys if (json.loads(Path('dist', key).read_text())['name'] == 'Not painted yet') == unpainted]
            assert subset == sorted(subset, reverse=True)
        for number in range(2, 22):
            p = Path('dist', wall_name, f'{number:02}.json')
            assert json.loads(p.read_text()) == {
                'name': 'Not painted yet',
                'image': 'https://api.imd.fun/artifacts/b5e794cb2c70bd232230e389707698c69c2080786d606a13b39f9315c9a90799',
                'attributes': [{'trait_type': 'Cave', 'value': 'Ice'}]}
            assert not p.with_suffix('.jpg').exists()
    for source, reused in [
        ('line-3/tools/import-map/import_map.py', 'shared/import-drift/import_map.py'),
        ('line-2/tools/csv-reconcile/reconcile.py', 'shared/import-drift/reconcile.py'),
        ('line-4/tools/abi-workbench/abi_workbench.py', 'shared/token-read-plan/abi_workbench.py'),
        ('line-2/tools/csv-patch/patch.py', 'shared/import-drift/patch.py'),
        ('line-1/tools/cache-lens/cache_lens.py', 'shared/http-evidence/cache_lens.py'),
        ('line-2/tools/csv-reconcile/reconcile.py', 'shared/http-evidence/reconcile.py')]:
        assert Path(source).read_bytes() == Path(reused).read_bytes()
    audit_source = Path('line-2/tools/csv-key-audit/audit.py').read_text().replace(
        "sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'csv-reconcile'))\n", '')
    assert audit_source == Path('shared/import-drift/audit.py').read_text()
    image_review = json.loads(Path('gathering/image-checks29.json').read_text())
    assert image_review['png']['sha256'] == digest
    assert image_review['preservation']['outside_rectangle_changed_pixels'] == 0
    assert image_review['preservation']['changed_pixels'] > 0
    assert json.loads(Path('gathering/test-runs29.json').read_text())['ok']
    assert json.loads(Path('gathering/integration-checks29.json').read_text())['ok']
    baseline = json.loads(Path('gathering/scope-before29.json').read_text())
    assert all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in baseline.items())
    actual = {p.as_posix() for n in range(1, 5) for root in (Path(f'line-{n}'), Path(f'dist/line-{n}')) for p in root.rglob('*') if p.is_file()}
    assert actual == set(baseline), 'line paths changed'
    for path in Path('gathering').rglob('*'):
        if path.is_file():
            assert path.stat().st_size < 100000, str(path)
    assert json.loads(Path('gathering/test-runs29.json').read_text())['gathering_tests'] == 8
    print(json.dumps({'ok': True, 'png': {'dimensions': [1254, 1254], 'format': 'PNG', 'sha256': digest, 'bytes': len(wall)},
                      'jpeg': {'dimensions': [512, 512], 'bytes': len(jpeg)},
                      'gallery_records': 145, 'painted_previews': 45, 'placeholders': 100,
                      'gallery_bytes': len(content.encode()),
                      'visual_certification': False}, indent=2))


if __name__ == '__main__':
    main()
