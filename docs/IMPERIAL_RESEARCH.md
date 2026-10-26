# Imperial undergraduate 2027 research collection

The official [Imperial course directory](https://www.imperial.ac.uk/study/courses/?courseType=undergraduate) showed 73 undergraduate results across seven pages when checked on 2026-10-26. Each result led to a current `/study/courses/undergraduate/2027/` course page. Those 73 official pages also presented 43 distinct study options. The collection contains 116 research records: one per primary listing or named option. The options share their parent official URL where Imperial presents them on one page.

The pages are **independent research material**. No record is approved for BTS publication or import. The collection was built without accessing the BTS importer or database. Imperial's course directory returned HTTP 403 through the ordinary web fetch; the current pages were read with the available site-scraping connector after checking Imperial's public robots file. Archived course-year paths were not visited. The source catalog stores brief factual values, not copied course descriptions or personal information.

## What was captured

The [source catalog](../data/imperial/undergraduate-2027.json) contains titles, qualifications, course duration, start date, study mode, department, location, UCAS code when explicitly shown, minimum entry standard, the application link when present, and the official course URL. It records an overseas 2027-entry tuition amount for 72 primary listings. Seventy fee headings explicitly say `per year`; two give only an amount, so their period remains null. The graduate-entry Medicine listing shows no overseas fee, so that field remains null. Study-option fees remain null because the primary course fee must not be assumed to apply to a year abroad, placement, or other option. An academic-year label is not inferred from the entry year.

Generated per-program JSON adds field-level status, source URL and locator. Values observed on an official course page are labelled `official_page_observed`; missing values are null and `unverified`. Language of instruction, English proficiency requirements, academic subject classification and BTS university slug remain unverified. The minimum entry standard is not a complete admissions assessment. A human must compare each record with the current official page before publication or import.

## Files and workflow

| Path | Purpose |
| --- | --- |
| `data/imperial/undergraduate-2027.json` | Compact, factual source catalog for 116 records. |
| `schema/imperial-program.schema.json` | Catalog schema. |
| `scripts/imperial.py` | Offline validation, duplicate detection, JSON/CSV export, and static HTML generation. |
| `site/programs/imperial/undergraduate/index.html` | Generated public directory linking to all 116 records. |
| `site/programs/imperial/undergraduate/*.html` | One generated page per record, each with Schema.org Course JSON-LD and an official source link. |
| `site/data/imperial/undergraduate/programs/*.json` | Generated records with per-field provenance. |
| `site/data/imperial/undergraduate/programs.csv` | Generated interoperability export. |

On Windows, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m scripts.pipeline validate
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scripts.pipeline build --base-url https://eladio12.github.io/bts-university-program-data
```

The public directory is `https://eladio12.github.io/bts-university-program-data/programs/imperial/undergraduate/`. A directory URL cannot be assumed to work with the current BTS importer: prior Cambridge review-only trials found zero candidates, and the importer’s discovery rules are unavailable. This Imperial collection has not been submitted to it.
