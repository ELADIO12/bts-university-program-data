# Cambridge undergraduate workbook research

The supplied 2027-entry workbook contains 32 undergraduate course listings in a 55-column BTS form table, plus READ ME and Tuition bands 2027 worksheets. The original three Oxford pilot JSON records and their URLs are separate. Cambridge's user-provided BTS university ID is 92862; no BTS lookup was performed.

## What was published

- A separate [Cambridge research directory](https://eladio12.github.io/bts-university-program-data/programs/cambridge/undergraduate/) with 32 individual pages, one per workbook row.
- A separate [Cambridge import-ready directory](https://eladio12.github.io/bts-university-program-data/programs/cambridge/undergraduate/import-ready/) with zero program links.
- One mapped JSON record per course, an exact cell-value raw workbook snapshot, aggregate JSON/CSV, a discovery manifest, excluded-program inventory, validation report, and source/duplicate/verification reports.

Research pages show workbook-reported values with their Excel cell coordinates and clear unverified status. No workbook value is promoted to an independently verified claim. Pages use semantic field headings and minimal Schema.org Course identity metadata with explicit hold status. They do not publish unsupported values as confirmed facts.

## Review blockers

1. All 32 workbook rows say `UNVERIFIED_LANGUAGE`. A general English-entry rule does not by itself establish that every compulsory component of each course is 100% English-taught. Modern-language and ancient-language courses need particular care.
2. The user reported three existing Cambridge BTS records but did not provide their titles or URLs. All 32 matches remain unknown. No three programs were arbitrarily removed or declared genuinely new.
3. In this research session, normal access to the Cambridge course directory, international-fees page, application-dates page, and entry-requirements page returned HTTP 403. No bypass or alternate-client retry was attempted. Official-source evidence must be collected through permitted manual access.
4. Only three workbook rows contain direct program URLs. The other 29 point to the Cambridge course directory, not a course-specific page. They need direct course-source identification.
5. One row, Medicine (Graduate course), has no workbook overseas tuition and is explicitly marked `EXCLUDE` in the supplied workbook. Its home fee, standard deadline, degree route and any special arrangements need individual review. The other 31 rows are on hold.
6. Annual home and overseas amounts are workbook-reported for 2027 entry, excluding College fees. The workbook does not explicitly label the tuition academic year; `tuition_academic_year` therefore remains null. Four-year BA/integrated routes and professional-course durations require checking.
7. The standard 2027-entry date in the workbook is 15 October 2026, which has passed as of this research pass. Individual exceptions and later intakes require review. The workbook's `Highly Competitive` label is an unsubstantiated editorial value, not an official Cambridge rating.

## Eligibility transition

The current Cambridge schema and validator intentionally allow only research intake. Before any record becomes import-ready, add an official evidence registry with per-field URLs, locators, dates, and human review, then extend the validator to require confirmed 100% English teaching, confirmed non-duplication against the existing Cambridge BTS inventory, and supported annual fees and course identity. Only reviewed records should appear in the import-ready directory. No code in this repository calls the BTS importer or database.

## Checks

Run `python -m scripts.pipeline validate`, `python -m unittest discover -s tests -v`, and `python -m scripts.pipeline build --base-url https://eladio12.github.io/bts-university-program-data`. The Cambridge tests reconcile all 32 Excel rows, 64 mapped BTS fields, tuition and duration to the workbook, unique identifiers, research-page links, an empty import-ready page, and the three Oxford URLs.
