# Surface Crystallography Archive

Query 1,379 historical surface-structure determinations and convert two archived LEED datasets into files readable by ViPErLEED.

## What you get

| Resource | Contents |
| --- | --- |
| **oSSD v8.1** | The original database and 11 JSON tables. All 428,409 exported cells were checked against an independent Microsoft Jet reader. |
| **Al(210)** | A converter for three archived diffraction curves: 390 energy–intensity pairs. The original paper used 14 beams; this is a subset. |
| **Ni(001)** | A converter for four curves: 701 pairs. Normal and 10-degree incidence remain separate. |

The oSSD data is included under CC0. The Stony Brook diffraction files are not bundled because redistribution rights remain unresolved. The converters accept exact local originals and preserve their samples without interpolation, smoothing or rescaling.

## Try it

Download the repository and use Python 3.12. No extra packages are needed for these commands:

```text
python surface_archive.py check-ossd
python surface_archive.py query --class-id 13.36
python surface_archive.py query --substrate Ag --min-year 1980
python surface_archive.py list
```

To convert a locally held reference file:

```text
python surface_archive.py convert al210 --source path/to/AL210.P_CLEAN --output local-al210
```

The output contains the original samples, EXPBEAMS CSV files and a provenance manifest. See [usage and verification](docs/USAGE.md) for source downloads, nickel conversion, optional ViPErLEED checks and database rebuilding.

## Sources and limits

P. R. Watson, M. A. Van Hove and K. Hermann created oSSD. Franco Jona and Jim Quinn curated the Stony Brook collection. The Al(210) experiment is by D. L. Adams, V. Jensen, X. F. Sun and J. H. Vollesen. The archived nickel reference is labelled unpublished; later publication has not been ruled out.

Autonomous AI research agents using OpenAI Codex built this software and performed the documented checks. They do not represent OpenAI. The checks establish faithful conversion and software import, not a reproduced scattering calculation or external scientific review.

[Sources and validation](docs/SOURCES.md) · [Data licenses](DATA_LICENSES.md) · [Citation](CITATION.cff)

Software: MIT. Bundled oSSD data: CC0 1.0.
