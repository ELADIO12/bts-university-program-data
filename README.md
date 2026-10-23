# BTS university program data — Oxford pilot and Cambridge research

A Python 3.12 static publishing pilot for **bts-university-program-data**. It turns reviewed Oxford facts into JSON, individual HTML pages, per-program completeness reports, a public directory and CSV. It has no backend, credentials, BTS connector or network-fetching code. No BTS production system was accessed or changed.

**Status:** the three Oxford pilot records remain partial and human-review pending. A separate Cambridge undergraduate collection contains 32 workbook-derived research records. None of the Cambridge records is import-ready: compulsory teaching language is unverified for all 32 and the identities of three existing Cambridge BTS programs were not provided. No record is approved for BTS publication.

## Cambridge undergraduate workbook collection

The [Cambridge research directory](https://eladio12.github.io/bts-university-program-data/programs/cambridge/undergraduate/) links to 32 individual research pages. The separate [BTS import-ready directory](https://eladio12.github.io/bts-university-program-data/programs/cambridge/undergraduate/import-ready/) is intentionally empty. Do not submit the research directory to the production-connected BTS importer.

For a manual importer compatibility check that reads only one URL, use the [self-contained Cambridge extraction page](https://eladio12.github.io/bts-university-program-data/programs/cambridge/undergraduate/all-programs.html). It places a compact set of workbook-reported fields for all 32 courses in the HTML, includes a 32-course Schema.org graph, and has no links to other pages or external assets. The individual research pages and JSON retain the full 64-field mapping. This is a **review-only test**: every record remains unverified or held. Stop at the review stage and do not confirm an import. The page may still be rejected by an importer that requires individual candidate URLs; compatibility can only be determined from the user's manual test.

The source workbook has three tabs: 32 course rows, a READ ME, and 2027 tuition bands. `data/cambridge/undergraduate/raw-workbook.json` preserves the supplied cell values and workbook SHA-256. `data/cambridge/undergraduate/programs/*.json` contains one mapped 64-field research record per row. `cambridge-undergraduate.json`, `cambridge-undergraduate.csv`, `discovery-manifest.json`, `excluded-programs.json`, and `validation-report.json` provide aggregate data and checks. The build copies these into the public site and produces three Cambridge reports under `site/reports/cambridge/`.

Workbook values are labelled `workbook_reported`, never `verified`. Three rows contain direct Cambridge course links; the other 29 use the Cambridge course directory as a research source. One graduate-entry Medicine row lacks an overseas fee and is explicitly excluded by the workbook; the other 31 are on hold. The workbook describes 2027-entry annual amounts but does not explicitly give an academic-year label, so that label remains null. Cambridge's official pages returned HTTP 403 during this research pass; no restriction was bypassed and official field verification requires permitted manual evidence.

To repeat workbook intake on Windows, install the dependencies above, then run:

```powershell
.\.venv\Scripts\python.exe -m scripts.cambridge ingest --workbook "C:\path\to\Cambridge_Undergraduate_BTS_Fields_2027_Research.xlsx"
.\.venv\Scripts\python.exe -m scripts.cambridge validate
.\.venv\Scripts\python.exe -m scripts.pipeline build --base-url https://eladio12.github.io/bts-university-program-data
```

Intake regenerates the Cambridge source JSON, CSV, manifest, and reports from the specified workbook. Review any locally curated changes before rerunning it. See [Cambridge research status](docs/CAMBRIDGE_RESEARCH.md) for the review queue and eligibility rules. The Cambridge intake has no BTS connection.

## Windows setup and checks

Install Python 3.12 and Git. In PowerShell, from this repository:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.pipeline validate
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scripts.pipeline build
.\.venv\Scripts\python.exe -m http.server 8000 --directory site
```

Open `http://localhost:8000/`. Virtual environment activation is unnecessary. The build and tests run offline once the dependency is installed. Run commands from the repository root. On macOS/Linux use `python3` for setup and `.venv/bin/python` afterward. `site/` is generated and ignored by Git; never edit it directly.

For a real hosting URL, supply the full repository base path:

```powershell
.\.venv\Scripts\python.exe -m scripts.pipeline build --base-url https://OWNER.github.io/bts-university-program-data
```

Replace `OWNER` with the actual account. No owner or public URL is assumed in the checked-in data. Canonical links and Schema.org `url` are omitted when no base URL is supplied. All internal navigation uses relative links and works under a GitHub project path.

## Pilot records and URLs

| Record | Relative public URL |
| --- | --- |
| Archaeology and Anthropology BA | `programs/oxford-archaeology-and-anthropology-ba.html` |
| Classical Archaeology and Ancient History BA | `programs/oxford-classical-archaeology-and-ancient-history-ba.html` |
| Archaeological Science MSc | `programs/oxford-archaeological-science-msc.html` |

The MSc was selected from [Oxford's School of Archaeology graduate directory](https://www.ox.ac.uk/admissions/graduate/courses/departments/archaeology). It is a standalone Master's course. Each record links to its original Oxford page; see the evidence register for access metadata and field locators.

## Files and data flow

| File or directory | Purpose |
| --- | --- |
| `data/programs/*.json` (3 files) | Curated source records, one per stable record ID. Edit these to update facts. |
| `data/evidence/*.json` (6 files) | Official-source access registers: five accessible sources and one application portal requiring manual evidence. Each stores URL, title, date, access outcome, method and limitations. No page copies or personal data. |
| `schema/program.schema.json` | Draft 2020-12 schema version 2.0: all 64 BTS form fields plus legacy source fields, types, nulls, dates and evidence. |
| `scripts/__init__.py` | Python package marker. |
| `scripts/pipeline.py` | Source validation, duplicate checks, HTML build, Course JSON-LD, completeness report/JSON copies and CSV export. No fetching or importer calls. |
| `scripts/bts.py` | BTS field vocabulary, tri-state validation, HTML section rendering and completeness calculation. |
| `templates/style.css` | Accessible, responsive visual styling; semantic HTML templates are in `pipeline.py`. |
| `tests/test_pipeline.py` | Schema/provenance failure cases, duplicate detection, serialization, HTML/JSON-LD escaping, CSV and build integration checks. |
| `.github/workflows/pages.yml` | Validate and test pull requests; build and deploy `main` with GitHub's Pages artifact workflow. |
| `requirements.txt` | Pinned direct JSON Schema validator dependency; transitive dependencies resolved by pip. |
| `.gitignore` | Excludes virtual environments, bytecode and generated website files. |
| `docs/BTS_IMPORTER_TEST_PLAN.md` | Manual sandbox-only importer protocol, modes, pass criteria and result template. |
| `docs/EVIDENCE_AND_REVIEW.md` | Collection policy, provenance semantics, source-specific assumptions and review workflow. |
| `docs/IMPLEMENTATION_REPORT.md` | Checks, deployment status and remaining review blockers. |
| `docs/BTS_FIELD_MAPPING.md` | Every BTS form field mapped to a record key, with population rules and adding-a-university steps. |
| `experiments/README.md` | Rules for keeping future synthetic importer fixtures separate from research data. |
| `README.md` | Setup, operation, deployment and file map. |

Generated by `build`:

| Output | Purpose |
| --- | --- |
| `site/index.html` | Directory linking all three individual pages and CSV. |
| `site/programs/*.html` | One semantic static page per program: facts, statuses, field provenance, official links and Course JSON-LD. No JavaScript execution needed to read facts. |
| `site/data/programs/*.json` | Unmodified copies of validated records. |
| `site/data/reports/*.json` | Per-program counts and review queues; completeness is not accuracy. |
| `site/data/evidence/*.json` | Evidence registers referenced by source IDs in records and CSV. |
| `site/data/programs.csv` | One row per record; values, statuses, provenance and review notes. Nested values are JSON within quoted CSV cells. Null values are blank, with status retained. |
| `site/assets/style.css` | Copied stylesheet. |
| `site/.nojekyll` | Keeps output as ordinary static files. |

The fixed `site/` directory belongs exclusively to the generator. A successful rebuild removes obsolete files there, so removed records do not leave stale public pages. Input validation happens before output changes. Do not place hand-authored content in `site/`.

## Integrity and review semantics

Each legacy research field contains `value`, `status`, `evidence` and `review_note`. The version 2.0 `bts_fields` object covers all 64 Add Program inputs; each of its fields adds `verified_on`, `academic_year` and `human_review_status`. See [the full mapping](docs/BTS_FIELD_MAPPING.md). `verified` means the factual value was checked against an accessible official source; it does **not** mean human approval or BTS acceptance. Every confirmed field has an evidence source ID, section locator and explanatory note. The record's verification date applies to its field checks. `human_review` remains `pending` and `publication_status` is always `research_only_not_approved` in this pilot.

Unknown values are null and `unverified`. BTS form flags are true, false, or null internally; null never becomes a checked or unchecked claim. `not_published`, `not_applicable`, `conflicting`, and `manual_evidence_required` are explicit review states when supported by the evidence workflow. Inaccessible-source facts must be null with `manual_evidence_required`; a blocked source cannot substantiate a verified value. Such fields are explicitly labeled in HTML, blank with status in CSV, and omitted from Course JSON-LD. All records remain partial while any field is unresolved. Requirements are concise summaries, not exhaustive admissions advice.

Duplicates are rejected by either normalized university identity + course title + qualification **or** university identity + canonical source URL. Normalization covers Unicode NFKC, case, punctuation, whitespace and `&` versus `and`. Source normalization drops query strings, fragments and trailing slashes. IDs and filenames must also be unique and match. This conservative source rule may reject legitimately distinct future variants sharing a page; review and extend the model before adding them. BA and MSc are explicit qualifications; synonym matching and fuzzy duplicates require human review.

Schema.org `Course` includes only confirmed facts. Annual Overseas fees stay in clearly scoped HTML/JSON/CSV rather than a generic `Offer`. Structured data does not prove that the BTS importer consumes JSON-LD. See [Schema.org Course](https://schema.org/Course).

## GitHub Pages deployment

The source is published in [ELADIO12/bts-university-program-data](https://github.com/ELADIO12/bts-university-program-data) on `main`. GitHub Pages uses the workflow in `.github/workflows/pages.yml` and serves the [public directory](https://eladio12.github.io/bts-university-program-data/). A dedicated GitHub noreply commit address is configured for this local checkout. Future updates should be reviewed in a branch and pull request before merging to `main`.

In **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**. Ensure Actions and the `github-pages` environment permit deployment from `main`. Rerun the workflow after enabling Pages if needed. Pull requests run validation/tests/build but cannot deploy. Pushes to `main`, or manual dispatch on `main`, build the same artifact and deploy it with `pages: write` and `id-token: write` limited to the deployment job. GitHub's configure-pages action supplies the actual base URL, including repository path/custom domain. See [GitHub's custom workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

The Pages workflow completed successfully and the public directory, three HTML pages, CSV and record JSON URLs returned HTTP 200 on 23 October 2026. Recheck the deployed revision after future changes. Importer compatibility still requires the isolated sandbox described below.

## BTS compatibility test

Follow [the complete test plan](docs/BTS_IMPORTER_TEST_PLAN.md). Use an isolated, owner-provided sandbox only. Do not submit URLs to a production-connected importer. Start with an individual program URL in **Programs Only** mode; compare its output to the exact generated record. Record what the importer actually reads and how it handles unknowns, provenance, fees and university matching. No automated test can assert compatibility with a private importer that is unavailable here.

## Adding new universities

Follow the six-step process in [the BTS field mapping](docs/BTS_FIELD_MAPPING.md). The official institutional domain in `university_identity` governs evidence URL validation; this is no longer Oxford-specific. Copy an existing version 2.0 record, assign a stable new ID, enter only sourced values, retain null for unknowns, then validate/test/build in a branch. The pipeline never scrapes university sites or invokes BTS. Review the generated HTML and per-program report before proposing publication.
