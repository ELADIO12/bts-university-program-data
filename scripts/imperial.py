"""Offline validation and static publishing for Imperial's 2027 undergraduate catalog.

The factual source snapshot was collected from official course pages. This module
does not fetch websites or contact BTS.
"""
from __future__ import annotations

import csv
import html
import io
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("data/imperial/undergraduate-2027.json")
SCHEMA = Path("schema/imperial-program.schema.json")
COLLECTION = "programs/imperial/undergraduate"
DATA = "data/imperial/undergraduate"
UNIVERSITY = "Imperial College London"
NOTICE = ("Independent research material. This is not an official Imperial College London website. "
          "Human review is pending; no record is approved for BTS publication or import.")
LABELS = {
    "program_title": "Program title",
    "qualification": "Degree qualification",
    "degree_level": "Study level",
    "duration": "Course duration",
    "start_date": "Start date",
    "study_mode": "Study mode",
    "locations": "Campus or location",
    "department": "Delivered by",
    "ucas_code": "UCAS course code",
    "minimum_entry_standard": "Minimum entry standard (not full requirements)",
    "overseas_fee": "Overseas tuition for 2027 entry",
    "application_url": "Application link",
    "language_of_instruction": "Language of instruction",
    "academic_subject": "Academic subject classification",
    "english_proficiency_requirements": "English proficiency requirements",
    "bts_university_slug": "BTS university slug",
}


def load(root: Path = ROOT) -> dict:
    return json.loads((root / SOURCE).read_text(encoding="utf-8"))


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("&", " and ")
    return " ".join(re.findall(r"\w+", value))


def validate(root: Path = ROOT) -> dict:
    catalog = load(root)
    schema = json.loads((root / SCHEMA).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(catalog)
    records = catalog["records"]
    if catalog["record_count"] != len(records):
        raise ValueError("Imperial catalog record count does not match records")
    ids, identities = set(), set()
    groups = defaultdict(list)
    for record in records:
        source = urlsplit(record["source_url"])
        if source.hostname != "www.imperial.ac.uk" or source.query or source.fragment:
            raise ValueError("Imperial source must be an official 2027 course URL")
        if record["id"] in ids:
            raise ValueError(f"Duplicate Imperial ID: {record['id']}")
        ids.add(record["id"])
        identity = (_normalized(UNIVERSITY), _normalized(record["title"]),
                    _normalized(record["qualification"]), record["source_url"].rstrip("/"))
        if identity in identities:
            raise ValueError(f"Duplicate Imperial program identity: {record['id']}")
        identities.add(identity)
        if record["option_index"] > 0 and record["overseas_fee"] is not None:
            raise ValueError("Study-option fee cannot be inferred from the primary course fee")
        if record["ucas_code"] and not re.fullmatch(r"[A-Z0-9]{4}", record["ucas_code"]):
            raise ValueError(f"Invalid UCAS code: {record['id']}")
        groups[record["listing_number"]].append(record)
    if len(groups) != catalog["directory_listing_count"]:
        raise ValueError("Imperial directory listing count does not match groups")
    if len({r["source_url"] for r in records}) != catalog["course_page_count"]:
        raise ValueError("Imperial source course page count does not match URLs")
    for number, group in groups.items():
        if sorted(r["option_index"] for r in group) != list(range(len(group))):
            raise ValueError(f"Missing or repeated study option in listing {number}")
        if len({r["source_url"] for r in group}) != 1:
            raise ValueError(f"Multiple source pages in listing {number}")
    return catalog


def site_files(catalog: dict) -> set[str]:
    names = {COLLECTION + "/index.html", DATA + "/catalog.json", DATA + "/programs.csv"}
    for record in catalog["records"]:
        names.add(COLLECTION + "/" + record["id"] + ".html")
        names.add(DATA + "/programs/" + record["id"] + ".json")
    return names


def _field(value, source_url: str, locator: str | None) -> dict:
    if value is None:
        return {"value": None, "status": "unverified", "source_url": None, "locator": None}
    return {"value": value, "status": "official_page_observed", "source_url": source_url,
            "locator": locator}


def public_record(record: dict, verification_date: str) -> dict:
    source = record["source_url"]
    option = record["option_index"] + 1
    facts = f"Course key facts, study option {option}"
    fields = {
        "program_title": _field(record["title"], source, "Course heading"),
        "qualification": _field(record["qualification"], source, facts + ": qualification"),
        "degree_level": _field("Undergraduate", source, "Course heading"),
        "duration": _field(record["duration"], source, facts + ": duration"),
        "start_date": _field(record["start_date"], source, facts + ": start date"),
        "study_mode": _field(record["study_mode"], source, facts + ": study mode"),
        "locations": _field(record["locations"], source, facts + ": location"),
        "department": _field(record["department"], source, facts + ": delivered by"),
        "ucas_code": _field(record["ucas_code"], source, facts + ": UCAS course code"),
        "minimum_entry_standard": _field(record["minimum_entry_standard"], source,
                                         facts + ": minimum entry standard"),
        "overseas_fee": _field(record["overseas_fee"], source, "Overseas fee, 2027 entry"),
        "application_url": _field(record["application_url"], source, "Application link beside course heading"),
        "language_of_instruction": _field(None, source, None),
        "academic_subject": _field(None, source, None),
        "english_proficiency_requirements": _field(None, source, None),
        "bts_university_slug": _field(None, source, None),
    }
    return {
        "id": record["id"], "university_name": UNIVERSITY,
        "source_url": source, "verification_date": verification_date,
        "directory_listing_number": record["listing_number"],
        "study_option_index": record["option_index"],
        "review_status": "human_review_pending", "bts_import_eligibility": "hold",
        "fields": fields,
    }


def _display(key: str, value) -> str:
    esc = html.escape
    if value is None:
        return "Not verified"
    if key == "overseas_fee":
        amount = f"GBP {value['amount_gbp']:,}"
        period = " per year" if value["period"] == "year" else " (period not stated in fee heading)"
        return esc(f"{amount}{period}; 2027 entry; academic-year label unverified")
    if isinstance(value, list):
        return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in value) + "</ul>"
    if key == "application_url":
        return f'<a href="{esc(value, quote=True)}">{esc(value)}</a>'
    return esc(str(value))


def _page(record: dict, base_url: str) -> str:
    esc = html.escape
    title = record["fields"]["program_title"]["value"]
    qualification = record["fields"]["qualification"]["value"]
    canonical = base_url.rstrip("/") + "/" + COLLECTION + "/" + record["id"] + ".html" if base_url else None
    course = {
        "@context": "https://schema.org", "@type": "Course", "name": title,
        "identifier": record["id"],
        "provider": {"@type": "CollegeOrUniversity", "name": UNIVERSITY},
        "isBasedOn": record["source_url"],
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Qualification", "value": qualification},
            {"@type": "PropertyValue", "name": "Review status", "value": "human review pending"},
            {"@type": "PropertyValue", "name": "BTS import eligibility", "value": "hold"},
        ],
    }
    if canonical:
        course["url"] = canonical
    structured = json.dumps(course, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    items = []
    for key, label in LABELS.items():
        field = record["fields"][key]
        detail = "Official course page observed" if field["status"] == "official_page_observed" else "Unverified"
        if field["locator"]:
            detail += "; " + field["locator"]
        items.append(f'<dt>{esc(label)}</dt><dd>{_display(key, field["value"])}'
                     f'<small>{esc(detail)}</small></dd>')
    body = (
        f'<h1>{esc(title)} — {esc(qualification)}</h1>'
        '<p>Imperial College London · Undergraduate · 2027 entry collection</p>'
        '<p><strong>Verification:</strong> Factual fields observed on the official course page; '
        'human review pending. BTS import eligibility: hold.</p>'
        f'<p><a href="{esc(record["source_url"], quote=True)}">Original Imperial course page</a> '
        f'· observed {esc(record["verification_date"])}.</p>'
        f'<p><a href="../../../data/imperial/undergraduate/programs/{esc(record["id"])}.json">'
        'Structured record with per-field provenance</a></p>'
        '<h2>Program facts</h2><dl>' + "".join(items) + '</dl>'
        '<p>Minimum entry standards are a summary of the course key facts, not complete admissions requirements. '
        'Fees for study options are omitted unless verified for that option.</p>'
    )
    canonical_tag = f'<link rel="canonical" href="{esc(canonical, quote=True)}">' if canonical else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{esc(title)} — {esc(qualification)} | Imperial research</title>'
        '<meta name="description" content="Independent Imperial undergraduate course facts for human review.">'
        '<link rel="stylesheet" href="../../../assets/style.css">'
        f'{canonical_tag}<script type="application/ld+json">{structured}</script></head><body>'
        '<header><strong>BTS · Imperial undergraduate research</strong></header><main>'
        f'<aside class="notice">{esc(NOTICE)}</aside>{body}</main>'
        '<footer>Check the official Imperial course page before using any value.</footer></body></html>'
    )


def _directory(catalog: dict, base_url: str) -> str:
    esc = html.escape
    groups = defaultdict(list)
    for record in catalog["records"]:
        groups[record["listing_number"]].append(record)
    sections = []
    for number in sorted(groups):
        group = sorted(groups[number], key=lambda item: item["option_index"])
        primary = group[0]
        links = []
        for item in group:
            suffix = " (study option)" if item["option_index"] else ""
            links.append(f'<li><a href="{esc(item["id"], quote=True)}.html">'
                         f'{esc(item["title"])} — {esc(item["qualification"])}</a>{suffix}</li>')
        sections.append(f'<section><h2>{esc(primary["title"])} — {esc(primary["qualification"])}</h2>'
                        f'<ul>{"".join(links)}</ul></section>')
    canonical = base_url.rstrip("/") + "/" + COLLECTION + "/" if base_url else None
    canonical_tag = f'<link rel="canonical" href="{esc(canonical, quote=True)}">' if canonical else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Imperial undergraduate 2027 program research directory</title>'
        '<meta name="description" content="Independent directory of Imperial undergraduate program research pages.">'
        f'<link rel="stylesheet" href="../../../assets/style.css">{canonical_tag}</head><body>'
        '<header><strong>BTS · Imperial undergraduate research</strong></header><main>'
        '<h1>Imperial College London — undergraduate programs for 2027 entry</h1>'
        f'<aside class="notice">{esc(NOTICE)}</aside>'
        f'<p>{len(groups)} primary course listings and {len(catalog["records"])} individual program '
        'and study-option research pages. Course descriptions are not reproduced.</p>'
        f'<p><a href="{esc(catalog["source_directory"], quote=True)}">Official Imperial course directory</a> '
        f'· observed {esc(catalog["verification_date"])}.</p>'
        '<p><a href="../../../data/imperial/undergraduate/programs.csv">Download factual research CSV</a> · '
        '<a href="../../../data/imperial/undergraduate/catalog.json">Source catalog JSON</a></p>'
        + "".join(sections) + '</main><footer>Human review required before any BTS use.</footer></body></html>'
    )


def _csv(records: list[dict]) -> str:
    output = io.StringIO(newline="")
    names = ["id", "title", "qualification", "source_url", "verification_date", "review_status",
             "bts_import_eligibility"] + list(LABELS)
    writer = csv.DictWriter(output, fieldnames=names)
    writer.writeheader()
    for record in records:
        row = {key: record[key] for key in names[:7] if key in record}
        row["title"] = record["fields"]["program_title"]["value"]
        row["qualification"] = record["fields"]["qualification"]["value"]
        for key in LABELS:
            value = record["fields"][key]["value"]
            row[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        writer.writerow(row)
    return output.getvalue()


def build(root: Path, out: Path, base_url: str = "") -> set[str]:
    catalog = validate(root)
    expected = site_files(catalog)
    def write(name: str, content: str) -> None:
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    write(COLLECTION + "/index.html", _directory(catalog, base_url))
    write(DATA + "/catalog.json", json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    published = []
    for source in catalog["records"]:
        record = public_record(source, catalog["verification_date"])
        published.append(record)
        write(COLLECTION + "/" + record["id"] + ".html", _page(record, base_url))
        write(DATA + "/programs/" + record["id"] + ".json",
              json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    write(DATA + "/programs.csv", _csv(published))
    return expected
