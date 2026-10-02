# Sources and limits

## oSSD

P. R. Watson, M. A. Van Hove and K. Hermann created the Surface Structure Database. The [custodial page](https://www.fhi.mpg.de/1017073/oSSD) and [Edmond deposit, DOI 10.17617/3.STDUDV](https://doi.org/10.17617/3.STDUDV), v8.1, preserve it. The deposit API's released version and CC0 terms were checked on 2026-10-02. The bundled MDB is exactly 4,816,896 bytes, SHA-256 `0311637a26d27dcb358735f8a34733e862b4f21a9968bb136150f4b7ae55e96b`.

Eleven non-system tables hold 1,379 determinations and 12,124 coordinate rows. An independent Microsoft Jet ODBC reader compared all 428,409 cells with the Python export. Five compressed-Unicode decoding errors were repaired against the original; see `evidence/parser-corrections.json`. These preserve source text, including possible original scientific typos. `evidence/export-audit.json` supplies hashes and counts. JSON uses UTF-8 and LF; prior Windows byte hashes are retained to distinguish serialization changes from value changes. Numeric publication years are 1969–2003, with five zero/unknown years, differing from the custodian's broad 1974–2004 description.

The table export is not a complete geometry interpretation. Fractional coordinates refer to the atom's layer cell; reference atoms and bulk repeats require reconstruction. Bulk repeat vectors can shift laterally. For ordered layers, source coverage is not automatically CIF occupancy. Do not treat absent uncertainty as zero uncertainty or emit simulation-ready slabs without reviewing these semantics.

## Stony Brook LEED references

Franco Jona and Jim Quinn curated the historical repository. Surviving [introduction](https://web.archive.org/web/20200811044945id_/http://dol1.eng.sunysb.edu/ivdata/intro.html), [reference list](https://web.archive.org/web/20200811043009id_/http://dol1.eng.sunysb.edu/ivdata/references.html) and [format guide](https://web.archive.org/web/20200811043718id_/http://dol1.eng.sunysb.edu/ivdata/data.html) explain its intended use for surface characterization and its fixed-width format. The guide already supplied a Fortran reader. Some spectra were digitized from articles; some beam indices were changed. This project preserves repository labels and does not silently map them to the oSSD crystallographic frame.

| Supported file | Provenance | Checked coverage |
| --- | --- | --- |
| `AL210.P_CLEAN` | D. L. Adams, V. Jensen, X. F. Sun and J. H. Vollesen, [Multilayer relaxation of the Al(210) surface, Physical Review B 38, 7913 (1988)](https://doi.org/10.1103/PhysRevB.38.7913) | 3 processed curves, 390 pairs, normal incidence. Paper used 14 beams at 135 K; this subset cannot reproduce the complete reported fit. oSSD class 13.36 matches the bibliography. |
| `NI100.P_CLEAN` | Stony Brook group; historical reference list says unpublished | 4 curves, 701 pairs. Normal incidence: 485 pairs; 10-degree incidence: 216. Four genuine zero-intensity values retained; seven trailing (0,0) format-padding pairs excluded. Later publication/current mirrors not excluded. |

Exact archived URLs, sizes and hashes are exposed by `python surface_archive.py list` and embedded in each local conversion manifest. An Internet Archive timestamp may redirect to an earlier capture; these URLs use the resolved source captures. SHA-256, not the requested date alone, fixes the bytes.

The two formats are deliberately bounded. The Ag(111) file was found but has repeated beam labels and is outside this release's supported conversions. This is not a general Stony Brook corpus converter. No spectra are included in the release.

## What the checks establish

For both supported files, a separate `fortranformat` decoder compares every energy/intensity pair, followed by actual ingestion with ViPErLEED 0.14.1. The Al original produces no beams or an error with the tested EXPBEAMS, TensErLEED and SATLEED readers; the conversion restores that software path. Existing [ViPErLEED utilities](https://www.viperleed.org/stable/content/calc/utilities/aux_to_exp.html) already cover other legacy layouts. No first-converter claim is made.

The result is exact source-preserving access. It does not establish detector accuracy, full experiment coverage, correct scattering parameters, an R-factor reproduction, global novelty or researcher adoption. Per-beam relative scales and historical processing remain; the converter performs no new interpolation, smoothing or rescaling. CSV NaNs indicate missing samples on the union of original energy grids. The [ViPErLEED input guide](https://www.viperleed.org/stable/content/calc/files/input/expbeams.html) describes further calculation constraints. Reader acceptance alone does not demonstrate a successful calculation.

Research selection, implementation and verification were performed by autonomous AI agents using OpenAI Codex. Original researchers and custodians supplied the scientific work and archived data. Agent checks are not external human review. The agents do not represent OpenAI.
