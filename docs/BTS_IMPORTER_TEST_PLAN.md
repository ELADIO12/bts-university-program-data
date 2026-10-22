# BTS URL importer compatibility test plan

## Question and current result

Can the existing URL + import-mode interface extract a single independent HTML program page hosted on GitHub Pages? **Not run; compatibility unknown.** The HTML is readable without JavaScript and contains labeled facts plus Schema.org Course JSON-LD; neither format guarantees importer support.

## Preconditions

- A repository owner has deployed the site and recorded its actual public HTTPS base URL and commit SHA.
- Check the directory and all three individual program URLs return HTTP 200 without login, and that the response body includes the facts and source/status labels.
- An authorized BTS operator supplies an isolated test importer that cannot write to the production database. Confirm that isolation before submitting anything. If only a production-connected importer exists, stop; document the blocker and request a dry-run or sandbox from its owner.
- Obtain a confirmed BTS university slug/matching rule for the sandbox if required. Do not guess a slug, change production identity mappings or silently create a second Oxford university.
- Review the source records and unresolved fields. Import outputs must be inspectable before persistence. Store no applicant/personal information in evidence.

## Test matrix

| Input | Mode | Inspect |
| --- | --- | --- |
| Individual BA Archaeology and Anthropology page | Programs Only | Exactly one program, linked to the sandbox Oxford identity if matching is supported |
| Individual BA Classical Archaeology and Ancient History page | Programs Only | Correct title/BA, distinct from the first BA; source and requirements preserved |
| Individual MSc Archaeological Science page | Programs Only | Exactly one standalone Master's; not an integrated undergraduate award |
| Repeat an individual URL | Programs Only | Whether importer deduplicates or proposes a duplicate; do not assume pipeline deduplication applies to importer |
| Individual program page | University + Programs | Whether it recognizes the provider and program; detect unintended new university creation in preview |
| Individual program page | University Only | Record whether university metadata is extracted or input rejected; no program should be persisted by the test operator |
| Directory URL | Programs Only | Optional discovery test: does it follow links or only parse the supplied page? |

Run the first three tests one at a time. The combined/university-only/directory tests are exploratory and do not determine the single-page objective. Do not accept a proposed import automatically. Do not use a production system as a fallback.

## Procedure and comparison

1. Freeze the deployed revision and retain its source JSON and generated CSV as the expected data. Record UTC time plus local time zone.
2. Submit one program URL and the selected mode in the isolated interface. Record any preview or error and elapsed time. Do not inspect or bypass importer internals.
3. Compare every extracted field with the record. Check title/qualification, level, duration units, study mode, Oxford identity, original source URL, annual GBP Overseas fees **and academic year**. Distinguish the independent input URL from Oxford's original source URL.
4. Confirm null language, unknown BTS slug and unknown BA location are not inferred as verified facts. Check whether review status, verification date and provenance survive; log omissions separately from incorrect facts. Check that independent-research notices are not ingested as course content.
5. Inspect whether the importer relied on labeled HTML, JSON-LD, linked JSON or unspecified behavior. If the interface does not reveal this, record **unknown**; successful extraction does not prove a particular mechanism.
6. Repeat for the other two records, then the repeat-URL test. If errors occur, retain the sanitized error and stop when further attempts would violate rate limits or safety boundaries.
7. Review outputs with the BTS owner. Leave all production records unchanged. Clean up only disposable sandbox records through its authorized owner.

## Pass/fail criteria

The single-page pilot passes only if all three direct program URLs produce exactly one correct program each in the isolated Programs Only preview, with no invented confirmed values, no conflation of the two BAs or Master's, and correctly scoped fee year/currency/status. Record whether missing fields stay null or absent. If review/provenance is dropped, mark the extraction technically readable but **not ready for unattended publication**. Failure to associate the university because its slug is unknown is a mapping blocker, not proof that HTML could not be read.

A blocked fetch, importer error, wrong qualification, unsupported fee scope, inferred unknown or silent duplicate is a documented failure requiring further design/review. No production-ready claim follows from a successful pilot.

## Result template (one per attempt)

```text
Test ID:
Operator / sandbox identifier (no secrets):
Confirmed isolation / owner:
UTC time and local time zone:
Deployment URL and commit SHA:
Input program URL:
Original Oxford source URL:
Import mode:
Expected record ID:
Importer version (if visible; otherwise unknown):
Outcome: NOT RUN / PASS / FAIL / BLOCKED
Extracted fields compared with expected values:
Null/unverified handling:
Fee scope and academic year:
University matching / duplicate behavior:
Source, verification date and provenance retained:
Observed extraction mechanism (or unknown):
Sanitized error / evidence location:
Sandbox cleanup status:
Follow-up owner and action:
```

Keep any future synthetic fixtures and sanitized test results in `experiments/`, never `data/programs/`. Never put tokens, session cookies, personal data or raw private importer screenshots in the public repository.
