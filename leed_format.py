"""Strict, source-documented Stony Brook/IBM numeric decoding.

Only explicitly mapped headers are accepted. Source bytes are authenticated by
surface_archive before this decoder runs. No interpolation or rescaling.
"""
import csv
from decimal import Decimal
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_stony_brook(raw, header_decoder=None, allow_trailing_zero_padding=False):
    """Strict documented 12F6.2 subset; reject ambiguity instead of guessing.

    Blank pairs are padding. With explicit opt-in, trailing (0,0) pairs are
    source-format padding; no later measurement may follow before beam end.
    Zero intensities at positive energy always survive.
    Terminator in column 80 can share a data record. Preserve post-stop text.
    No support is claimed for all historical format variants or arbitrary headers.
    """
    lines = raw.decode('ascii').splitlines()
    beams, current = [], None
    padding_started = False
    for number, line in enumerate(lines, 1):
        if line[:4].lower() == 'stop':
            if current is not None or not beams:
                raise ValueError(f'Unexpected stop at line {number}')
            return beams, b''.join(raw.splitlines(keepends=True)[number:]).decode('ascii')
        if not line.strip():
            continue
        if current is None:
            padding_started = False
            if header_decoder is not None:
                current = {**header_decoder(line), 'header': line.rstrip(), 'points': []}
                continue
            match = re.fullmatch(r'&& Al\{210\},(-?\d+) (-?\d+) Beam,Adams etal,Theta=0,\d+,Al210\.[abc]\s*', line)
            if not match:
                raise ValueError(f'Unrecognized beam header at line {number}')
            current = {'hk': tuple(map(int, match.groups())), 'header': line.rstrip(), 'points': []}
            continue
        if len(line) > 80 or line[76:79].strip() or (line[79:80] not in ('', ' ', '5')):
            raise ValueError(f'Unexpected control columns at line {number}')
        payload = line[:72].ljust(72)
        for offset in range(0, 72, 12):
            energy, intensity = payload[offset:offset+6], payload[offset+6:offset+12]
            if not energy.strip() and not intensity.strip():
                continue
            if not energy.strip() or not intensity.strip():
                raise ValueError(f'Partial numeric pair at line {number}')
            e, i = Decimal(energy), Decimal(intensity)
            if allow_trailing_zero_padding and e == 0 and i == 0:
                padding_started = True
                continue
            if padding_started:
                raise ValueError(f'Measurement follows zero padding at line {number}')
            if not e.is_finite() or not i.is_finite() or e <= 0 or i < 0:
                raise ValueError(f'Invalid value at line {number}')
            if current['points'] and e <= current['points'][-1][0]:
                raise ValueError(f'Non-increasing energy at line {number}')
            current['points'].append((e, i))
        if line[79:80] == '5':
            if not current['points'] or current['hk'] in [b['hk'] for b in beams]:
                raise ValueError('Empty or duplicate beam')
            beams.append(current)
            current = None
    raise ValueError('Missing file stop marker')


def write_csv(beams, path):
    """A union of original energy coordinates; NaN means no point for that beam."""
    points = [dict(b['points']) for b in beams]
    energies = sorted({e for b in beams for e, _ in b['points']})
    with path.open('w', newline='', encoding='ascii') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['E'] + [f'({h}|{k})' for h, k in (b['hk'] for b in beams)])
        for energy in energies:
            writer.writerow([str(energy)] + [str(p.get(energy, 'NaN')) for p in points])

