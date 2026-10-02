# Software, data and provenance

Original software and documentation in this release are offered under the MIT license, to the extent any copyright or related rights exist. This does not assert that an AI agent is a legal owner. Third-party data and dependencies have their own terms.

| Material | Source and terms | Included? |
| --- | --- | --- |
| `data/oSSD2003.mdb` | [K. Hermann's Edmond deposit](https://doi.org/10.17617/3.STDUDV), released v8.1, CC0 1.0 | Yes, unchanged original |
| `data/*.json` | Faithful derived exports of the CC0 database; source field names retained; five source-checked Unicode fixes documented | Yes, CC0 source data |
| Stony Brook numerical spectra and converted curves | Historical archive; no explicit redistribution license established | No |
| Synthetic tests | Invented values written by this project's agents, not experimental data | Yes, MIT |
| Python dependencies | Installed separately under their own licenses | No vendored dependencies |

The [CC0 1.0 legal text](https://creativecommons.org/publicdomain/zero/1.0/legalcode) applies to the deposited database. Cite the scientific sources even where attribution is not a license condition. Watson, Van Hove and Hermann created the database; this project's JSON serialization, access code and checks are subsequent agent contributions. They are not depositor-issued files or new measurements.

The archive's public accessibility and historical “unpublished” label do not establish permission to redistribute its spectra. The explicit `fetch` command retrieves a pinned public archived source into a local cache; it grants no additional rights. The conversion command requires a locally held exact source. Check the rights applicable to your intended use before sharing source or derived numerical files. The oSSD deposit's CC0 status does not apply to Stony Brook files. Do not submit those files or CSV/JSON derivatives in contributions without documented rights.

Dependencies are not copied into this release. The optional ViPErLEED checker imports the installed package; its code is not included. The format decoder is an original Python implementation informed by the source format description, not a copy of the historical Fortran routine.
