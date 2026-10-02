"""Portable access to two pinned LEED references and the CC0 oSSD table export."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from tempfile import TemporaryDirectory
from pathlib import Path
from urllib.request import Request, urlopen

from leed_format import parse_stony_brook, require, write_csv

VERSION = '0.1.0'
ROOT = Path(__file__).resolve().parent
CATALOG = {
    'al210': {
        'name': 'Al(210)-(1x1)', 'file': 'AL210.P_CLEAN',
        'url': 'https://web.archive.org/web/20200811042919id_/http://dol1.eng.sunysb.edu/ivdata/data/AL210.P_CLEAN',
        'sha256': '96db42db9552794a81972653c8cca9bd3c3e7f07932523fa2505c9404d18ff66',
        'bytes': 6966, 'counts': [120, 132, 138],
        'attribution': 'D. L. Adams, V. Jensen, X. F. Sun, J. H. Vollesen; Stony Brook repository curators',
        'source_doi': '10.1103/PhysRevB.38.7913', 'ossd_class_id': '13.36',
        'limits': 'Three processed repository curves, versus fourteen beams in the source paper. Not a full-fit reproduction or raw instrument data.',
    },
    'ni001': {
        'name': 'Ni(001)-(1x1)', 'file': 'NI100.P_CLEAN',
        'url': 'https://web.archive.org/web/20200811041457id_/http://dol1.eng.sunysb.edu/ivdata/data/NI100.P_CLEAN',
        'sha256': 'af896eb1c4cbd594bdc1428b7b1f245ce4b550fb00ff0c47eb9a7dab591beaff',
        'bytes': 10287, 'counts': [209, 172, 104, 216],
        'attribution': 'Stony Brook group; historical reference list labels this dataset unpublished',
        'source_doi': None, 'ossd_class_id': None,
        'limits': 'Later publication/current mirror not excluded. Sample conditions and beam frame unvalidated. Separate normal and ten-degree incidence.',
    },
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def authenticated_source(dataset, path):
    raw = path.read_bytes()
    source = CATALOG[dataset]
    require(len(raw) == source['bytes'] and sha256(raw) == source['sha256'],
            'Source hash/size differs from the catalog. No conversion performed; do not rename another file as this source.')
    return raw


def decode(dataset, raw):
    def header(line):
        if dataset == 'al210':
            match = re.fullmatch(r'&& Al\{210\},(-?\d+) (-?\d+) Beam,Adams etal,Theta=0,\d+,Al210\.[abc]\s*', line)
            require(match is not None, 'Unknown Al210 header')
            h, k = map(int, match.groups())
            return {'hk': (h, k), 'theta_deg': 0, 'phi_deg': None}
        match = re.fullmatch(r'&& ([012])([01]) beam NI\(001\)\(1X1\) TH=(0|10) PH=0 FENI03\.H[124]\s*', line)
        require(match is not None, 'Unknown Ni001 header')
        h, k, theta = map(int, match.groups())
        return {'hk': (h, k), 'theta_deg': theta, 'phi_deg': 0}
    beams, tail = parse_stony_brook(raw, header_decoder=header,
                                  allow_trailing_zero_padding=dataset == 'ni001')
    require([len(b['points']) for b in beams] == CATALOG[dataset]['counts'],
            'Unexpected beam or point counts')
    return beams, tail


def fetch(dataset, cache):
    """Only an explicit fetch command uses the network; existing bytes are checked."""
    source = CATALOG[dataset]
    destination = cache / source['file']
    if destination.exists():
        authenticated_source(dataset, destination)
        return destination
    with urlopen(Request(source['url'], headers={'User-Agent': 'surface-crystallography-archive/0.1'}), timeout=40) as response:
        raw = response.read(source['bytes'] + 1)
    require(len(raw) == source['bytes'] and sha256(raw) == source['sha256'],
            'Downloaded bytes differ from the pinned source; nothing saved')
    cache.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as handle:
        handle.write(raw)
    return destination


def canonical_curves(beams):
    return [{'curve_id': index + 1, 'header': beam['header'],
             'hk': list(beam['hk']), 'theta_deg': beam['theta_deg'], 'phi_deg': beam['phi_deg'],
             'energy_unit': 'eV', 'intensity_unit': 'relative source units',
             'points': [[str(e), str(i)] for e, i in beam['points']]}
            for index, beam in enumerate(beams)]


def _write_conversion(dataset, beams, tail, output):
    products = []
    for theta in sorted({b['theta_deg'] for b in beams}):
        selected = [b for b in beams if b['theta_deg'] == theta]
        path = output / f'theta{theta}-EXPBEAMS.csv'
        write_csv(selected, path)
        products.append({'file': path.name, 'sha256': sha256(path.read_bytes()),
                         'theta_deg': theta, 'beams': len(selected),
                         'points': sum(len(b['points']) for b in selected)})
    canonical = canonical_curves(beams)
    (output / 'curves.json').write_text(json.dumps(canonical, indent=2)+'\n', encoding='utf-8', newline='\n')
    (output / 'post-stop.txt').write_bytes(tail.encode('ascii'))
    manifest = {'schema_version': 1, 'software_version': VERSION, 'dataset': dataset,
                'source': CATALOG[dataset], 'outputs': products,
                'curves_sha256': sha256((output/'curves.json').read_bytes()),
                'post_stop_sha256': sha256(tail.encode('ascii')),
                'transformations': 'No interpolation, smoothing, renormalization or invented samples. CSV NaN means absent sample; original per-beam grids retained.',
                'padding': 'Trailing (0,0) format padding excluded for Ni; genuine zero intensity at positive energy retained.',
                'rights': 'No Stony Brook redistribution license established; acquisition does not grant redistribution rights.',
                'scientific_status': 'Source-faithful import only; no scattering fit or experimental validation. Beam frames and sample conditions require review.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8', newline='\n')
    return manifest


def convert(dataset, source_path, output):
    raw = authenticated_source(dataset, source_path)
    beams, tail = decode(dataset, raw)
    require(not output.exists(), 'Output directory already exists; choose a new directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.surface-archive-', dir=output.parent) as temporary:
        staging = Path(temporary)
        manifest = _write_conversion(dataset, beams, tail, staging)
        require(not output.exists(), 'Output directory appeared during conversion; not overwriting it')
        staging.rename(output)
    return manifest


def check_source_products(expected, tail, output):
    require(json.loads((output/'curves.json').read_text(encoding='utf-8')) == canonical_curves(expected),
            'Canonical curves differ from authenticated source')
    require((output/'post-stop.txt').read_bytes() == tail.encode('ascii'),
            'Post-stop bytes differ from authenticated source')


def verify_conversion(dataset, source_path, output):
    """Actual ViPErLEED ingestion plus independent Fortran-format decoding."""
    try:
        from fortranformat import FortranRecordReader
        from viperleed.calc.files.beams import readOUTBEAMS
        from importlib.metadata import version
    except ImportError as exc:
        raise ValueError('Verification dependencies missing; install requirements.lock.txt') from exc
    raw = authenticated_source(dataset, source_path)
    expected, tail = decode(dataset, raw)
    check_source_products(expected, tail, output)
    reader = FortranRecordReader('(12F6.2)')
    blocks = raw.decode('ascii').split('stop', 1)[0].split('&& ')[1:]
    require(len(blocks) == len(expected), 'Independent decoder block-count mismatch')
    for block, beam in zip(blocks, expected):
        values = []
        for line in block.splitlines()[1:]:
            if not line[:72].strip():
                continue
            numbers = reader.read(line)
            values += [(e, i) for e, i in zip(numbers[0::2], numbers[1::2])
                       if e is not None and i is not None and e > 0]
        require(values == [(float(e), float(i)) for e, i in beam['points']],
                'Independent numeric decoder disagrees')
    manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    require(manifest['dataset'] == dataset and manifest['source'] == CATALOG[dataset], 'Manifest source mismatch')
    for key, file in [('curves_sha256', 'curves.json'), ('post_stop_sha256', 'post-stop.txt')]:
        require(sha256((output/file).read_bytes()) == manifest[key], f'Changed {file}')
    require([p['theta_deg'] for p in manifest['outputs']] == sorted({b['theta_deg'] for b in expected}), 'Incidence-group mismatch')
    checked = 0
    for item in manifest['outputs']:
        file = f"theta{item['theta_deg']}-EXPBEAMS.csv"
        require(item['file'] == file, 'Unexpected output path')
        require(sha256((output/file).read_bytes()) == item['sha256'], 'CSV hash mismatch')
        loaded = readOUTBEAMS(str(output/file))
        selected = [b for b in expected if b['theta_deg'] == item['theta_deg']]
        require(item['beams'] == len(selected) and item['points'] == sum(len(b['points']) for b in selected),
                'Manifest beam/point counts disagree with source')
        require(len(loaded) == len(selected), 'ViPErLEED beam-count mismatch')
        for actual, original in zip(loaded, selected):
            require(tuple(actual.hk) == original['hk'], 'Beam labels changed')
            require(actual.intens == {float(e): float(i) for e, i in original['points']}, 'Numerical values changed or disappeared')
            checked += len(actual.intens)
    return {'result': 'passed', 'dataset': dataset, 'pairs_checked': checked,
            'viperleed': version('viperleed'), 'fortranformat': version('fortranformat'),
            'scope': 'Exact software ingestion; no scientific fit or external review'}


def verify_ossd(data_dir):
    audit = json.loads((ROOT/'evidence/export-audit.json').read_text(encoding='utf-8'))
    require(sha256((data_dir/'oSSD2003.mdb').read_bytes()) == audit['source_sha256'], 'MDB hash mismatch')
    for name, metadata in audit['tables'].items():
        raw = (data_dir/f'{name}.json').read_bytes()
        require(sha256(raw) == metadata['sha256'], f'{name} hash mismatch')
        rows = json.loads(raw)
        require(len(rows) == metadata['rows'], f'{name} row-count mismatch')
    return {'result': 'passed', 'tables': len(audit['tables']),
            'scope': 'Bundled bytes match recorded independent ODBC-checked export; this does not rerun ODBC'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='Show the two supported pinned sources and their limitations')
    p = sub.add_parser('fetch', help='Explicitly download a pinned public source; check rights before redistribution')
    p.add_argument('dataset', choices=CATALOG); p.add_argument('--cache', type=Path, default=Path('.local/leed'))
    for name in ['convert', 'verify']:
        p = sub.add_parser(name, help='Offline conversion' if name=='convert' else 'Verify with independent decoder and ViPErLEED')
        p.add_argument('dataset', choices=CATALOG); p.add_argument('--source', type=Path, required=True)
        p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('check-ossd', help='Check the bundled CC0 database and table hashes')
    p.add_argument('--data', type=Path, default=ROOT/'data')
    p = sub.add_parser('query', help='Query CC0 oSSD records without dependencies')
    p.add_argument('--data', type=Path, default=ROOT/'data')
    p.add_argument('--substrate'); p.add_argument('--class-id'); p.add_argument('--min-year', type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == 'list':
            result = CATALOG
        elif args.command == 'fetch':
            result = {'file': str(fetch(args.dataset, args.cache)), 'status': 'source hash verified'}
        elif args.command == 'convert':
            result = convert(args.dataset, args.source, args.output)
        elif args.command == 'verify':
            result = verify_conversion(args.dataset, args.source, args.output)
        elif args.command == 'check-ossd':
            result = verify_ossd(args.data)
        else:
            verify_ossd(args.data)
            rows = json.loads((args.data/'MAIN.json').read_text(encoding='utf-8'))
            result = [r for r in rows if (args.substrate is None or r['Substrate'] == args.substrate)
                      and (args.class_id is None or r['Class #'] == args.class_id)
                      and (args.min_year is None or r['Year'] >= args.min_year)]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
