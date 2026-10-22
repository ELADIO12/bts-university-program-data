# Evidence collection and review

Research date: 2026-10-23 (Asia/Manila). The official course pages and graduate department directory were accessible through the web research tool. The build never downloads Oxford pages. The evidence registers are research logs, not archived page snapshots or independently signed evidence. A human should corroborate the locators before any operational use.

## Authoritative sources

- [Archaeology and Anthropology BA](https://www.ox.ac.uk/admissions/undergraduate/courses/course-listing/archaeology-and-anthropology): title, BA, undergraduate level, duration, full-time mode, subject, requirements and 2027 entry Overseas fees.
- [Classical Archaeology and Ancient History BA](https://www.ox.ac.uk/admissions/undergraduate/courses/course-listing/classical-archaeology-and-ancient-history): equivalent course fields; its IB score differs from the other BA.
- [MSc in Archaeological Science](https://www.ox.ac.uk/admissions/graduate/courses/msc-archaeological-science): award, duration, attendance, location, entry/English requirements, annual Overseas fees and application guidance.
- [School of Archaeology graduate directory](https://www.ox.ac.uk/admissions/graduate/courses/departments/archaeology): current standalone MSc listing.
- [Undergraduate application guidance](https://www.ox.ac.uk/admissions/undergraduate/applying): application route for the BAs.

Only short factual extractions and researcher-written summaries are retained. No marketing descriptions, images, staff contacts, applicant data or page dumps are copied.

## Assumptions and limits

- `university_identity = ox.ac.uk` is a local normalized identity based on the official domain. It is not a BTS identifier. The BTS university slug remains null because no confirmed mapping was provided.
- Qualification codes, subject names and degree-level categories are normalized from the official titles/headings; locators identify that transformation. MSc title is stored without its qualification prefix; its official heading is recorded in the review note.
- The BA fees are labeled for 2027 entry on Oxford's pages. `2027-28` is the normalized corresponding academic year and the review notes disclose this. The MSc page explicitly labels the same academic year. All fees are annual Overseas tuition, excluding living costs/additional charges; do not treat them as total degree costs.
- BA location remains null because an explicit course location was not captured as a standalone field during this review. Do not infer a campus from college references. MSc location is supported by its Attendance and Resources sections.
- Language of instruction remains null for all three courses. English admission requirements do not alone establish the language of every component of teaching.
- Application URLs intentionally point to accessible Oxford application **guidance**. The linked MSc eVision application login failed one research-tool fetch with a cache-miss error. No login was attempted and no retries or workaround were used. Its usability requires manual evidence collection; the record does not claim the login works.
- Entry/English requirements are summaries. BA accepted-test thresholds were not captured. MSc IELTS is one accepted test, not a complete list. Follow the source for exemptions, alternatives, document rules and international equivalencies.
- `verified` is source verification by this research pass. All records still require human review; no record claims Oxford endorsement or BTS approval.

## Updating records

1. Open the official source through normal allowed access. Respect robots restrictions, rate limits, access denials, CAPTCHA and login boundaries. Stop on restrictions; never rotate identities, proxies or clients to evade a denial.
2. If unavailable, record `access_status: manual_evidence_required`, keep unsupported field values null with the same field status, and explain the failure. Ask an authorized reviewer to obtain evidence through permitted means. Never fill gaps from search snippets or assumptions.
3. For accessible material, record the date, URL, method and section locator. Write only the brief facts needed. Edit the source JSON; do not edit generated pages. All dates must be real and no later than verification.
4. Update field evidence and verification date together. Run validation, tests and build; inspect the generated pages and CSV. A change in fee year or requirements warrants a fresh review.
5. Review in a branch/PR. This pilot intentionally has no approval transition; introducing human approval needs an explicit future schema/workflow change. Never convert a record to production publication by changing a label.

Evidence failures are explicit data states, not a reason for a crawler to retry. No automated scraping is included.
