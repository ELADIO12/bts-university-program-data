# Implementation and verification report

Delivered 2026-10-23. Public GitHub repository: `ELADIO12/bts-university-program-data`, branch `main`. The source was committed and pushed; GitHub Pages is enabled from the Actions workflow. No BTS production system was accessed or changed.

## Completed

- Three Oxford records: the two requested BAs and the standalone Archaeological Science MSc selected from the official graduate directory.
- Seventeen fields per record, each with value, source-check status, evidence references and review notes. Record-level verification date, pending human review and fixed research-only publication status.
- JSON Schema plus offline semantic validation for provenance references, institutional domain boundaries, accessible evidence, dates, filenames, duplicate IDs and duplicate course identities/source URLs.
- Deterministic static HTML build with a directory, one stable URL per program, 13 requested semantic sections, definition lists, metadata, Course JSON-LD, official source links and independent-research notice.
- JSON/evidence downloads, completeness reports and CSV export preserving status and provenance. Source records, generated pages and future synthetic experiments are separated.
- GitHub Actions PR checks and `main` Pages artifact deployment, Windows setup and sandbox-only BTS test instructions.

## Checks actually run

| Check | Result |
| --- | --- |
| `python -m scripts.pipeline validate` | PASS: 3 records |
| `python -W error::ResourceWarning -m unittest discover -s tests -v` | PASS: 48 tests |
| `python -m scripts.pipeline build` | PASS: generated static site |
| `python -m compileall -q scripts tests` | PASS |
| Local HTTP responses | PASS: HTTP 200 for all 19 generated files |
| Browser review | Directory layout inspected; individual MSc navigation and accessible content verified |
| Git whitespace check | PASS: staged source files |
| GitHub Actions execution / live Pages deployment | PASS: workflow run 39848415892 at commit `1579aa5`; public directory HTTP 200 |
| BTS importer execution | NOT RUN: isolated importer unavailable |

Checks used bundled Python 3.12 with `jsonschema` 4.23.0 installed into workspace-only tooling. The system `python` command resolves to an unavailable Windows Store alias; the README gives normal `py -3.12` virtual environment instructions. No dependency binaries or virtual environments are included in the repository. No external source fetch happens during any test/build.

The automated tests cover missing/unsupported values, invalid types/dates/fee year, missing or inaccessible/nonofficial evidence, publication-status claims, normalized duplicate identity and URL collisions, CSV and JSON round trips, script/HTML and CSV formula escaping, internal links under a repository base path, directory coverage, generated source copies, Course JSON-LD omission of unknowns, deterministic rebuilds, stale output removal and failure on invalid input before publishing.

## Acceptance assessment

| Criterion | Status |
| --- | --- |
| All tests pass | Met locally: 48/48 |
| GitHub Pages deploys successfully | Met: live workflow and public URL verified |
| Individual program URLs | Met: all three public URLs returned HTTP 200 |
| Directory links all pilot records | Met and tested |
| Pages identify source and verification status | Met and tested; browser checked on MSc |
| Unsupported fields not shown as confirmed facts | Met: null/status handling; omitted from JSON-LD |
| Documented importer compatibility plan | Met: `docs/BTS_IMPORTER_TEST_PLAN.md` |
| No BTS production changes | Met: no production access or importer connection |

## Remaining review and external blockers

1. Continue human review in a pull request for future updates. The initial pilot is already deployed; a future change should be checked against its own successful Pages run.
2. Supply an isolated BTS sandbox/dry-run importer and a confirmed BTS university slug. Execute the documented matrix; never fall back to a production-connected importer. Compatibility remains unknown.
3. Human review is pending for every source extraction. The BTS slug and all instruction-language fields remain null; BA location is also null. The pipeline does not claim these records are complete or approved.
4. The MSc application guidance page was accessible; one fetch of its linked eVision login returned a research-tool cache miss. Its usability requires manual evidence collection; no authentication/retry/workaround was attempted. The published application field is explicitly a guidance URL.
5. BA fee year is normalized from Oxford's 2027 entry label to 2027-28 and disclosed as such. Requirements are summaries; accepted tests, exemptions and full conditions must be checked at the official source before an operational import.

See `README.md` for every source/generated file and commands, and `docs/EVIDENCE_AND_REVIEW.md` for source-specific assumptions and access policy. The generated preview has no invented owner, canonical URL or BTS approval label. The source archive includes a generated `site/` for convenience; Git ignores that directory and CI rebuilds it. The public directory, all three HTML pages, CSV and three program JSON files returned HTTP 200 on 2026-10-23.

## BTS Add Program upgrade

Schema version 2.0 now requires all 64 mapped BTS form fields per record. Oxford MSc completeness: 29 verified / 35 missing; each BA: 22 verified / 42 missing. All fields still await human review. The score measures sourced coverage, not accuracy. The three stable program URLs are unchanged. Annual Home/Overseas GBP tuition, fee year, distinct deadlines, duration choice and tri-state flags are visible in ordinary HTML and exported in JSON/CSV. The [field mapping](BTS_FIELD_MAPPING.md) lists every form key and the adding-a-university workflow. The BTS importer has not been contacted.
