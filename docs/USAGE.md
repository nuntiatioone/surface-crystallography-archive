# Usage and verification

## Start without installing dependencies

Open a terminal in the extracted release directory. These commands work in PowerShell and a Unix shell:

```text
python surface_archive.py check-ossd
python surface_archive.py query --class-id 13.36
python surface_archive.py query --substrate Ag --min-year 1980
python surface_archive.py list
python -m unittest discover -s tests -v
```

Expected: eleven tables pass integrity checks; class 13.36 returns the 1988 Al(210) determination; the silver query returns 52 records. Queries emit JSON and can be redirected to a file. Class identifiers are strings, not numeric keys. oSSD values retain source fields, units, unknowns and publication-year discrepancies. See the source guide before interpreting coordinates or uncertainties.

## Convert a locally held LEED source

The release does **not** contain Stony Brook spectra or their numerical derivatives: no redistribution license has been established. If you hold the exact original from a permitted source:

```text
python surface_archive.py convert ni001 --source path/to/NI100.P_CLEAN --output local-ni001
python surface_archive.py convert al210 --source path/to/AL210.P_CLEAN --output local-al210
```

Replace the source paths with your files. The destination must be new; existing work is never overwritten. Conversion is offline. A mismatched source hash is a hard error, including under optimized Python. This intentionally supports the two pinned files rather than guessing the meaning of arbitrary LEED data.

Each output directory contains:

- `curves.json`: original decimal samples, beam labels, incidence metadata and source headers.
- `theta0-EXPBEAMS.csv`: normal-incidence curves; Ni also has a separate `theta10-EXPBEAMS.csv`.
- `post-stop.txt`: preserved trailing source metadata, excluded from measurement parsing.
- `manifest.json`: original URL, source and output hashes, processing statements, provenance and limitations.

The original energy grids are retained. CSV NaNs are absent samples, not interpolated measurements. Genuine zero intensities are retained. No normalization or smoothing is added. Beam labels are repository labels; their crystallographic-frame correspondence is not independently established.

An explicit optional acquisition command can retrieve a pinned public archived file. It does not grant reuse or redistribution rights:

```text
python surface_archive.py fetch ni001 --cache .local/leed
python surface_archive.py fetch al210 --cache .local/leed
```

Only `fetch` uses the network. It verifies the source before saving it and rechecks any cached file. If the archive is unavailable, an authorized local original works equally well; a different capture must match the published hash. No automatic retries or corpus scraping are performed.

## Verify actual ViPErLEED ingestion

Optional dependencies are isolated in a virtual environment. Install the pinned set from this release:

```text
python -m venv .venv
```

Windows: `.venv/Scripts/python.exe -m pip install -r requirements.lock.txt`

Linux/macOS: `.venv/bin/python -m pip install -r requirements.lock.txt`

Use that environment's Python executable for these commands:

```text
python surface_archive.py verify ni001 --source path/to/NI100.P_CLEAN --output local-ni001
python surface_archive.py verify al210 --source path/to/AL210.P_CLEAN --output local-al210
```

Verification independently decodes every numeric pair with `fortranformat`, checks output integrity, and loads each CSV through ViPErLEED 0.14.1. Expected counts are 701 and 390. It writes no new evidence or numerical files. A full scattering calculation needs validated geometry, beam frames, experimental conditions and scattering inputs; reader acceptance alone is not such a calculation.

## Rebuild the oSSD table export

Install `requirements-export.txt` in a local environment, then run:

```text
python inspect_ossd.py --output .local/ossd-rebuilt
```

Every regenerated table must exactly match the bundled, independently checked baseline before anything is written. This portable check uses the original MDB, preserves the five documented Unicode corrections, and writes to a new directory. It does not overwrite the reference data. The original Microsoft Jet/ODBC comparison was performed on Windows; that historical all-cell check is documented in `evidence/independent-check.json`. Rebuilding the bytes is distinct from repeating that independent-reader experiment.

## Validation and contribution scope

Eight offline tests cover source tampering under `python -O`, truncation, unknown headers, duplicate beam labels, zero intensities, format padding, overwrite prevention, table integrity and a useful database query. The workflow in `.github/workflows/check.yml` is prepared for Windows and Ubuntu. Local Windows checks are recorded in `evidence/release-validation.json`; GitHub-hosted CI and other operating systems are unverified until run there.

Changes should preserve original bytes, source labels, units and explicit unknowns. Supply provenance and a focused failing test for any decoder change. Unsupported datasets need separate review of format, scientific metadata and reuse rights. Do not upload restricted spectra or derived curves in issues or pull requests. No maintainer response time or ongoing automated archival service is promised.

Software: MIT. Bundled oSSD source/exports: CC0 1.0. Third-party spectra: excluded, with rights unresolved. This is an inspectable access release, not a claim of a new experiment, complete historical recovery, or a validated scientific fit.
