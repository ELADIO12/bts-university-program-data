# BTS Add Program field mapping

The `bts_fields` object is the form-shaped research layer. The older `fields` object remains for compatibility with the original pilot and for identity/duplicate checks. All values are independent research data, never a BTS database write.

Every `bts_fields` entry has `value`, `status`, `evidence` (source ID, section locator and note), `verified_on`, `academic_year` when relevant, `human_review_status`, and `review_note`. Source IDs resolve to URL and page title in `data/evidence/`. `verified` means checked against accessible official evidence, not human approval. Null with `unverified`, `conflicting`, `not_published`, `not_applicable`, or `manual_evidence_required` must not be imported as a fact.

## Form mapping

| Page section | BTS form label | Record key | Notes |
| --- | --- | --- | --- |
| Program Overview | Program Title | `program_title` | Official evidence or null. |
| Program Overview | Degree Level | `degree_level` | Official evidence or null. |
| Program Overview | School Name | `school_name` | Official evidence or null. |
| Program Overview | Program Link | `program_link` | HTTPS URL. |
| Program Overview | Contact (University) | `contact_university` | Official evidence or null. |
| Degree and Academic Information | Degree Type | `degree_type` | Official evidence or null. |
| Areas of Study | Areas of Study | `areas_of_study` | Official evidence or null. |
| Areas of Study | Primary Area of Study (BTS category) | `primary_area_of_study` | Official evidence or null. |
| Areas of Study | Additional Areas of Study (BTS categories) | `additional_areas_of_study` | Official evidence or null. |
| Program Description | Description | `description_html` | Official evidence or null. |
| Location | University Street | `university_street` | Official evidence or null. |
| Location | University Street 2 | `university_street_2` | Official evidence or null. |
| Location | University Postal Code | `university_postal_code` | Official evidence or null. |
| Location | University City | `university_city` | Official evidence or null. |
| Location | University Region | `university_region` | Official evidence or null. |
| Location | University Country | `university_country` | Official evidence or null. |
| Location | University Latitude | `university_latitude` | Official evidence or null. |
| Location | University Longitude | `university_longitude` | Official evidence or null. |
| Location | Program Street | `program_street` | Official evidence or null. |
| Location | Program Street 2 | `program_street_2` | Official evidence or null. |
| Location | Program Postal Code | `program_postal_code` | Official evidence or null. |
| Location | Program City | `program_city` | Official evidence or null. |
| Location | Program Region | `program_region` | Official evidence or null. |
| Location | Program Country | `program_country` | Official evidence or null. |
| Location | Program Latitude | `program_latitude` | Official evidence or null. |
| Location | Program Longitude | `program_longitude` | Official evidence or null. |
| Location | Inherit university location | `inherit_university_location` | Tri-state: true, false, or null (unknown). |
| Study Format and Duration | Format | `format` | Official evidence or null. |
| Study Format and Duration | Attendance | `attendance` | Official evidence or null. |
| Study Format and Duration | Published duration | `duration_original` | Published duration and dropdown are separate. |
| Study Format and Duration | BTS duration choice | `duration_bts` | Published duration and dropdown are separate. |
| Annual Tuition and Fee Year | Annual home tuition | `tuition_home` | GBP annual fee object with year and fee status. |
| Annual Tuition and Fee Year | Annual non-EU / overseas tuition | `tuition_non_eu` | GBP annual fee object with year and fee status. |
| Annual Tuition and Fee Year | Original tuition currency | `tuition_currency` | Official evidence or null. |
| Annual Tuition and Fee Year | Tuition academic year | `tuition_academic_year` | Official evidence or null. |
| Annual Tuition and Fee Year | Tuition source URL | `tuition_source_url` | HTTPS URL. |
| Annual Tuition and Fee Year | Tuition last verified | `tuition_last_verified` | ISO date internally. |
| Annual Tuition and Fee Year | Tuition billing period | `tuition_billing_period` | Official evidence or null. |
| Annual Tuition and Fee Year | EUR conversion (only when needed) | `tuition_conversion` | Official evidence or null. |
| Application Deadlines | Application Deadline | `application_deadline` | Official evidence or null. |
| Application Deadlines | Application Deadline Date | `application_deadline_date` | ISO date internally. |
| Application Deadlines | Scholarship consideration deadline | `scholarship_deadline` | ISO date internally. |
| Application Deadlines | Final admission deadline | `final_admission_deadline` | ISO date internally. |
| Application Deadlines | Application opening date | `application_opening_date` | ISO date internally. |
| Application Deadlines | Expected start date | `expected_start_date` | ISO date internally. |
| Application Deadlines | Start Your Application URL | `start_application_url` | HTTPS URL. |
| Admissions Requirements | Admissions Requirements | `admissions_requirements` | Official evidence or null. |
| Admissions Requirements | Admissions Difficulty (BTS editorial) | `admissions_difficulty` | Official evidence or null. |
| Admissions Requirements | Minimum GPA | `minimum_gpa` | Official evidence or null. |
| English Language Requirements | English Proficiency Required (non-US) | `english_proficiency_required` | Tri-state: true, false, or null (unknown). |
| English Language Requirements | English tests and scores | `english_tests` | Official evidence or null. |
| Tests and Special Requirements | Entrance Exam | `entrance_exam` | Tri-state: true, false, or null (unknown). |
| Tests and Special Requirements | GMAT/GRE Required | `gmat_gre_required` | Tri-state: true, false, or null (unknown). |
| Tests and Special Requirements | SAT / ACT Required | `sat_act_required` | Tri-state: true, false, or null (unknown). |
| Tests and Special Requirements | APS Required | `aps_required` | Official evidence or null. |
| Additional Program Flags | Numerus Fixus | `numerus_fixus` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | Pre-Master | `pre_master` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | Foundation Year | `foundation_year` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | Post-Bachelor Work Experience | `post_bachelor_work_experience` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | Erasmus Mundus | `erasmus_mundus` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | American School | `american_school` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | Franchise | `franchise` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | Spring Intake | `spring_intake` | Tri-state: true, false, or null (unknown). |
| Additional Program Flags | Internship Built In | `internship_built_in` | Tri-state: true, false, or null (unknown). |

`tuition_non_eu` maps to the BTS “Tuition (non-EU)” input; `tuition_home` maps to “Tuition”. Both retain GBP, annual period and academic year. The generated page says this explicitly. No total-degree multiplication occurs. EUR conversion stays null unless an authoritative rate/date is supplied; the original GBP amount must remain alongside it.

`application_deadline` is a readable label while `application_deadline_date` is the final admissions ISO date. Scholarship consideration is separate. For the MSc the January deadline is for scholarship consideration and March is the final admissions deadline.

`degree_level` is normalized to `Bachelors` or `Masters`; `degree_type` retains BA or MSc. `areas_of_study` contains subjects supported by Oxford; the primary and additional **BTS taxonomy categories** stay unknown until the actual taxonomy is provided. `admissions_difficulty` is null until a documented BTS editorial assessment is made. No undergraduate IELTS test score or language of instruction is inferred from admission policies.

Program location and university-level address are distinct. An absent program teaching address does not imply a verified Oxford-wide street address. `inherit_university_location` remains unknown until a reviewer confirms the intended BTS location mapping.

## Current completeness

| Program | Total | Verified | Missing | Conflicting | Human review fields |
| --- | ---: | ---: | ---: | ---: | ---: |
| oxford-archaeological-science-msc | 64 | 29 | 35 | 0 | 64 |
| oxford-archaeology-and-anthropology-ba | 64 | 22 | 42 | 0 | 64 |
| oxford-classical-archaeology-and-ancient-history-ba | 64 | 22 | 42 | 0 | 64 |

The completeness percentage only counts fields populated with official evidence. It is not an accuracy score or permission to import. All fields remain pending human review.

## Adding a university or program

1. Add one evidence register per official accessible source in `data/evidence/`, with institution domain, title, URL, access status and check date. Respect access controls; blocked pages are marked for manual collection.
2. Copy a record under `data/programs/` with a stable unique ID/filename and `schema_version` 2.0. Supply every key in `fields` and `bts_fields`; use null with status and note where evidence is absent. `university_identity` is its official domain for source-domain validation.
3. Keep every field tied to an accessible institutional URL and section locator. The publisher does no scraping. Do not use generic university requirements as course-specific facts without course evidence.
4. Verify degree, fee billing period and year, application deadlines, duration mapping and tri-state flags. Keep the original published currency. Only add conversion with original amount, rate, date and converted amount.
5. Run `python -m scripts.pipeline validate`, `python -m unittest discover -s tests -v`, and `python -m scripts.pipeline build --base-url <Pages base URL>`. Review HTML/CSV/reports and open a PR. Identical normalized course identity or source URL is rejected before output changes.
6. Compare the public program URL with the BTS importer only in the authorized review flow. This repository never calls the importer.
