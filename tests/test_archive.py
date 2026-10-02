"""Network-free tests use invented measurements, never archived spectra."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from leed_format import parse_stony_brook
import surface_archive as archive


def fixture(points, header='&& synthetic', zero_padding=False):
    numeric = ''.join(f'{e:6.2f}{i:6.2f}' for e, i in points)
    if zero_padding:
        numeric += f'{0:6.2f}{0:6.2f}'
    return (header+'\n'+numeric.ljust(72)+'\n'+' '*79+'5\nstop\nsynthetic provenance\n').encode('ascii')


def synthetic_header(line):
    if line != '&& synthetic':
        raise ValueError('Unknown synthetic header')
    return {'hk': (1, 0), 'theta_deg': 0, 'phi_deg': 0}


class FormatTests(unittest.TestCase):
    def test_real_zero_intensity_preserved_and_tail_separate(self):
        beams, tail = parse_stony_brook(fixture([(10, 1), (11, 0), (12, 2)]), synthetic_header)
        self.assertEqual([float(i) for _, i in beams[0]['points']], [1, 0, 2])
        self.assertEqual(tail, 'synthetic provenance\n')

    def test_padding_is_explicit_and_only_trailing(self):
        raw = fixture([(10, 1)], zero_padding=True)
        with self.assertRaises(ValueError):
            parse_stony_brook(raw, synthetic_header)
        beams, _ = parse_stony_brook(raw, synthetic_header, True)
        self.assertEqual(len(beams[0]['points']), 1)
        bad = fixture([(10, 1), (0, 0), (11, 2)])
        with self.assertRaisesRegex(ValueError, 'follows zero padding'):
            parse_stony_brook(bad, synthetic_header, True)

    def test_corruption_rejected(self):
        valid = fixture([(10, 1), (11, 2)])
        cases = [valid.split(b'stop')[0], valid.replace(b' '*79+b'5\n', b''),
                 valid.replace(b'&& synthetic', b'&& unknown'),
                 fixture([(10, 1), (10, 2)]), fixture([(10, -1)]),
                 valid.replace(b' 10.00  1.00', b' 10.00      ')]
        for raw in cases:
            with self.subTest(raw=raw[:40]), self.assertRaises((ValueError, ArithmeticError)):
                parse_stony_brook(raw, synthetic_header)

    def test_duplicate_labels_are_not_silently_merged(self):
        raw = fixture([(10, 1)]).split(b'stop')[0]*2+b'stop\n'
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            parse_stony_brook(raw, synthetic_header)


class ReleaseTests(unittest.TestCase):
    def test_source_hash_failure_writes_nothing_even_optimized(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'bad'; source.write_bytes(b'untrusted bytes')
            output = Path(tmp)/'out'
            result = subprocess.run([sys.executable, '-O', str(archive.ROOT/'surface_archive.py'),
                                     'convert', 'ni001', '--source', str(source), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('hash/size', result.stderr)
            self.assertFalse(output.exists())

    def test_convert_is_offline_and_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'source'
            source.write_bytes(fixture([(10, 1), (11, 0)],
                '&& Al{210},0 -1 Beam,Adams etal,Theta=0,1003,Al210.a'))
            spec = dict(archive.CATALOG['al210'], bytes=source.stat().st_size,
                        sha256=archive.sha256(source.read_bytes()), counts=[2])
            output = Path(tmp)/'out'
            with patch.dict(archive.CATALOG, {'al210': spec}), patch.object(archive, 'urlopen', side_effect=AssertionError('Network called')):
                report = archive.convert('al210', source, output)
                self.assertEqual(report['outputs'][0]['points'], 2)
                curves = json.loads((output/'curves.json').read_text())
                self.assertEqual(curves[0]['points'][1], ['11.00', '0.00'])
                original = (output/'curves.json').read_bytes()
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    archive.convert('al210', source, output)
                self.assertEqual((output/'curves.json').read_bytes(), original)

    def test_output_metadata_cannot_replace_source_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            beams, tail = parse_stony_brook(fixture([(10, 1)]), synthetic_header)
            (out/'curves.json').write_text(json.dumps(archive.canonical_curves(beams)))
            (out/'post-stop.txt').write_bytes(tail.encode('ascii'))
            archive.check_source_products(beams, tail, out)
            changed = archive.canonical_curves(beams)
            changed[0]['points'][0][1] = '99.00'
            (out/'curves.json').write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, 'Canonical curves'):
                archive.check_source_products(beams, tail, out)
            (out/'curves.json').write_text(json.dumps(archive.canonical_curves(beams)))
            (out/'post-stop.txt').write_bytes(b'altered processing history')
            with self.assertRaisesRegex(ValueError, 'Post-stop'):
                archive.check_source_products(beams, tail, out)

    def test_bundled_ossd_and_query(self):
        self.assertEqual(archive.verify_ossd(archive.ROOT/'data')['tables'], 11)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(archive.main(['query', '--class-id', '13.36']), 0)
        rows = json.loads(output.getvalue())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Name'], 'Al(210)-(1x1)')


if __name__ == '__main__':
    unittest.main()
