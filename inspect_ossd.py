"""Reproduce the pinned CC0 export without overwriting bundled reference tables."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from access_parser import AccessParser
from leed_format import require

ROOT = Path(__file__).resolve().parent


def encode(value):
    if isinstance(value, bytes):
        return {'type': 'bytes', 'base64': base64.b64encode(value).decode('ascii')}
    raise TypeError(type(value).__name__)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'data/oSSD2003.mdb')
    parser.add_argument('--output', type=Path, default=Path('.local/ossd-rebuilt'))
    args = parser.parse_args(argv)
    raw = args.source.read_bytes()
    expected = json.loads((ROOT/'evidence/export-audit.json').read_text(encoding='utf-8'))
    require(len(raw) == 4816896 and hashlib.sha256(raw).hexdigest() == expected['source_sha256'],
            'MDB differs from the pinned original; nothing exported')
    require(not args.output.exists(), 'Output directory exists; choose a new directory')
    corrections = json.loads((ROOT/'evidence/parser-corrections.json').read_text(encoding='utf-8'))
    db = AccessParser(str(args.source))
    exported = {}
    for name in sorted(db.catalog):
        if name.startswith('MSys'):
            continue
        table = db.parse_table(name)
        lengths = {len(v) for v in table.values()}
        require(len(lengths) == 1, f'Inconsistent column lengths: {name}')
        columns = list(table)
        rows = [dict(zip(columns, row)) for row in zip(*(table[c] for c in columns))]
        for fix in corrections['corrections']:
            if fix['table'] != name:
                continue
            row = rows[fix['row']]
            require(row['Class #'] == fix['class_id'] and row[fix['column']] == fix['python'],
                    f'Source-pinned Unicode correction no longer matches: {name}')
            row[fix['column']] = fix['odbc']
        text = json.dumps(rows, ensure_ascii=False, indent=2, default=encode, allow_nan=False) + '\n'
        payload = text.encode('utf-8')
        require(name in expected['tables'], f'Unexpected table: {name}')
        require(hashlib.sha256(payload).hexdigest() == expected['tables'][name]['sha256'],
                f'Rebuilt table disagrees with checked baseline: {name}')
        exported[name] = payload
    require(set(exported) == set(expected['tables']), 'Table coverage differs from baseline')
    args.output.mkdir(parents=True)
    for name, payload in exported.items():
        (args.output/f'{name}.json').write_bytes(payload)
    print(json.dumps({'result': 'passed', 'tables': len(exported),
                     'comparison': 'All table bytes match independently ODBC-checked baseline',
                     'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
