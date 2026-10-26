"""Offline publishing pipeline: no university or BTS network requests."""
from __future__ import annotations
import argparse
import csv
import html
import io
import json
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from jsonschema import Draft202012Validator, FormatChecker
from . import bts, cambridge, imperial

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    'university_name': 'University name', 'university_identity': 'University identity',
    'bts_university_slug': 'BTS university slug', 'program_title': 'Program title',
    'qualification': 'Degree qualification', 'degree_level': 'Degree level',
    'academic_subject': 'Academic subject', 'duration': 'Course duration',
    'study_mode': 'Study mode', 'location': 'Campus / location',
    'language_of_instruction': 'Language of instruction',
    'international_tuition': 'International tuition', 'entry_requirements': 'Entry requirements (summary)',
    'english_requirements': 'English proficiency requirements (summary)',
    'application_url': 'Application guidance URL', 'source_url': 'Original university source URL',
    'summary': 'Factual summary',
}
NOTICE = ('Independent research material for the BTS importer pilot. '
          'This is not an official Oxford website. No record is approved for BTS publication.')


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)


def normalized(text):
    text = unicodedata.normalize('NFKC', text).casefold().replace('&', ' and ')
    return ' '.join(re.findall(r'\w+', text, flags=re.UNICODE))


def canonical_source(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'), '', ''))


def official(url, university_domain):
    parts = urlsplit(url)
    return parts.scheme == 'https' and (parts.hostname == university_domain or
            (parts.hostname or '').endswith('.' + university_domain)) and not parts.username


def validate(records, evidence, root=ROOT):
    schema = read_json(root / 'schema/program.schema.json')
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    ids, identities, sources = set(), set(), set()
    for record in records:
        validator.validate(record)
        rid = record['id']
        if rid in ids:
            raise ValueError(f'Duplicate record id: {rid}')
        ids.add(rid)
        fields = record['fields']
        if set(fields) != set(FIELDS):
            raise ValueError(f'{rid}: unexpected or missing fields')
        values = {key: field['value'] for key, field in fields.items()}
        domain = values['university_identity'].lower()
        if not re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)+', domain):
            raise ValueError(f'{rid}: invalid institutional domain')
        identity = tuple(normalized(values[k]) for k in
                         ('university_identity', 'program_title', 'qualification'))
        source = (identity[0], canonical_source(values['source_url']))
        if identity in identities or source in sources:
            raise ValueError(f'Duplicate program identity or source: {rid}')
        identities.add(identity)
        sources.add(source)
        verification = date.fromisoformat(record['verification_date'])
        # Verification dates are recorded in the project's Asia/Manila time zone.
        if verification > datetime.now(timezone(timedelta(hours=8))).date():
            raise ValueError(f'{rid}: future verification date')
        for name, field in fields.items():
            verified = field['status'] == 'verified'
            if verified != (field['value'] is not None):
                raise ValueError(f'{rid}.{name}: only verified fields may contain facts')
            if verified and not field['evidence']:
                raise ValueError(f'{rid}.{name}: evidence required')
            for item in field['evidence']:
                src = evidence.get(item['source_id'])
                if not src or not official(src.get('url', ''), domain):
                    raise ValueError(f'{rid}.{name}: missing or non-Oxford evidence')
                accessed = date.fromisoformat(src['accessed_on'])
                if accessed > verification:
                    raise ValueError(f'{rid}.{name}: evidence newer than verification')
                if verified and src['access_status'] != 'accessible':
                    raise ValueError(f'{rid}.{name}: inaccessible evidence cannot verify a fact')
            if name in ('application_url', 'source_url') and verified and not official(field['value'], domain):
                raise ValueError(f'{rid}.{name}: expected official Oxford URL')
        if not any(evidence[e['source_id']]['url'] == values['source_url']
                   for e in fields['source_url']['evidence']):
            raise ValueError(f'{rid}: original source must match its evidence URL')
        expected = 'verified' if all(f['status'] == 'verified' for f in fields.values()) else 'partial'
        bts.validate_bts(record, evidence)
        if record['review_status'] != expected:
            raise ValueError(f'{rid}: incorrect overall review status')
    if not records:
        raise ValueError('No course records found')


def load(root=ROOT):
    evidence = {}
    for path in sorted((root / 'data/evidence').glob('*.json')):
        src = read_json(path)
        required = {'id', 'url', 'title', 'accessed_on', 'access_status', 'method', 'note'}
        if set(src) != required or src['id'] in evidence:
            raise ValueError(f'Invalid or duplicate evidence file: {path.name}')
        if src['access_status'] not in ('accessible', 'manual_evidence_required'):
            raise ValueError(f'Invalid evidence access status: {path.name}')
        if urlsplit(src['url']).scheme != 'https' or not urlsplit(src['url']).hostname or not all(isinstance(v, str) and v.strip() for v in src.values()):
            raise ValueError(f'Invalid evidence metadata: {path.name}')
        date.fromisoformat(src['accessed_on'])
        evidence[src['id']] = src
    records = []
    for path in sorted((root / 'data/programs').glob('*.json')):
        record = read_json(path)
        if path.stem != record['id']:
            raise ValueError(f'Filename must match record id: {path.name}')
        records.append(record)
    validate(records, evidence, root)
    return records, evidence


def confirmed(record, key):
    field = record['fields'][key]
    return field['value'] if field['status'] == 'verified' else None


def display(value):
    if value is None:
        return 'Not verified — no confirmed value'
    if isinstance(value, dict):
        if 'currency' in value:
            return (f"{value['currency']} {value['amount']:,} per {value['period']}; "
                    f"{value['academic_year']}; {value['fee_status']}. {value['note']}")
        return f"{value['amount']} {value['unit']}"
    return str(value)


def course_jsonld(record, base_url):
    get = lambda key: confirmed(record, key)
    data = {'@context': 'https://schema.org', '@type': 'Course',
            'name': get('program_title'), 'identifier': record['id'],
            'provider': {'@type': 'CollegeOrUniversity', 'name': get('university_name')},
            'isBasedOn': get('source_url')}
    if base_url:
        data['url'] = base_url.rstrip('/') + '/programs/' + record['id'] + '.html'
    mapping = {'summary': 'description', 'qualification': 'educationalCredentialAwarded',
               'degree_level': 'educationalLevel', 'academic_subject': 'about',
               'language_of_instruction': 'inLanguage', 'entry_requirements': 'coursePrerequisites'}
    for key, prop in mapping.items():
        if get(key) is not None:
            data[prop] = {'@type': 'DefinedTerm', 'name': get(key)} if prop == 'about' else get(key)
    duration = get('duration')
    if duration:
        data['timeRequired'] = f"P{duration['amount']}{'Y' if duration['unit'] == 'years' else 'M'}"
    instance = {'@type': 'CourseInstance'}
    if get('study_mode'):
        instance['courseMode'] = get('study_mode')
    if get('location'):
        instance['location'] = {'@type': 'Place', 'name': get('location')}
    if len(instance) > 1:
        data['hasCourseInstance'] = instance
    # Overseas annual fees are not a generally purchasable Offer.
    return data


def page(title, body, prefix='', structured=None, canonical=None):
    esc = html.escape
    metadata = ''
    if structured:
        safe = json.dumps(structured, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        metadata += f'<script type="application/ld+json">{safe}</script>'
    if canonical:
        metadata += f'<link rel="canonical" href="{esc(canonical, quote=True)}">'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | BTS research pilot</title>
<meta name="description" content="Independent Oxford program research with field-level evidence and verification status.">
<link rel="stylesheet" href="{prefix}assets/style.css">{metadata}</head>
<body><header><a href="{prefix}index.html">BTS · University program research</a><p>OXFORD PILOT / EXPERIMENTAL</p></header>
<main><aside class="notice" aria-label="Independence notice">{NOTICE}</aside>{body}</main>
<footer>Source verification is a research check, not an admissions guarantee. Consult Oxford for current details.</footer></body></html>'''


def program_page(record, evidence, base_url):
    esc = html.escape
    title = confirmed(record, 'program_title')
    report = bts.completeness(record)
    body = (f'<h1>{esc(title)} — {esc(confirmed(record, "qualification"))}</h1>'
            f'<p>University: {esc(confirmed(record, "university_name"))}</p>'
            f'<p>Review status: <strong>{record["review_status"]}</strong>. '
            f'Verification date: <time datetime="{record["verification_date"]}">{record["verification_date"]}</time>. '
            'Human review pending.</p><p>Requirements below are brief summaries; consult linked official sources for full conditions.</p>'
            f'<p><a href="../data/programs/{record["id"]}.json">Source record (JSON)</a> · '
            f'<a href="../data/reports/{record["id"]}.json">Field completeness report (JSON)</a></p>'
            f'<p>Field completeness: {report["verified_fields"]} of {report["total_fields"]} populated with official evidence. '
            'This is not an accuracy or approval score.</p>'
            + bts.render_bts(record, evidence))
    canonical = base_url.rstrip('/') + '/programs/' + record['id'] + '.html' if base_url else None
    return page(title, body, '../', course_jsonld(record, base_url), canonical)


def export_csv(records):
    output = io.StringIO(newline='')
    columns = ['id', 'verification_date', 'review_status']
    for field in FIELDS:
        columns.extend([field, field + '_status', field + '_provenance', field + '_review_note'])
    for field in bts.LABELS:
        columns.extend(['bts_' + field, 'bts_' + field + '_status', 'bts_' + field + '_provenance'])
    writer = csv.DictWriter(output, columns, lineterminator='\n')
    writer.writeheader()
    for record in records:
        row = {key: record[key] for key in ('id', 'verification_date', 'review_status')}
        for field in FIELDS:
            value = confirmed(record, field)
            cell = '' if value is None else json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else str(value)
            if cell.lstrip().startswith(('=', '+', '-', '@')):
                cell = "'" + cell
            row[field] = cell
            row[field + '_status'] = record['fields'][field]['status']
            row[field + '_provenance'] = json.dumps(record['fields'][field]['evidence'], ensure_ascii=False)
            row[field + '_review_note'] = record['fields'][field]['review_note']
        for field in bts.LABELS:
            item = record['bts_fields'][field]
            value = item['value'] if item['status'] == 'verified' else None
            cell = '' if value is None else json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
            if cell.lstrip().startswith(('=', '+', '-', '@')):
                cell = "'" + cell
            row['bts_' + field] = cell
            row['bts_' + field + '_status'] = item['status']
            row['bts_' + field + '_provenance'] = json.dumps(item['evidence'], ensure_ascii=False)
        writer.writerow(row)
    return output.getvalue()


def build(root=ROOT, base_url=''):
    if base_url:
        parts = urlsplit(base_url)
        if parts.scheme != 'https' or not parts.hostname or parts.query or parts.fragment or parts.username:
            raise ValueError('Base URL must be an HTTPS site URL, optionally with repository path')
    records, evidence = load(root)
    cambridge_records, _ = cambridge.load(root)
    if cambridge_records:
        cambridge.validate(root)
    imperial_catalog = imperial.validate(root)
    out = root / 'site'
    expected = {'index.html', '.nojekyll', 'assets/style.css', 'data/programs.csv'}
    for record in records:
        expected.update({f'programs/{record["id"]}.html', f'data/programs/{record["id"]}.json', f'data/reports/{record["id"]}.json'})
    expected.update(f'data/evidence/{key}.json' for key in evidence)
    expected.update(cambridge.site_files(cambridge_records))
    expected.update(imperial.site_files(imperial_catalog))
    if out.is_symlink():
        raise ValueError('Generated site directory must not be a symlink')
    for path in out.rglob('*') if out.exists() else []:
        if path.is_symlink():
            raise ValueError('Symlinks are not allowed in generated output')
        if path.is_file() and path.relative_to(out).as_posix() not in expected:
            path.unlink()
    def write(name, content):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8', newline='\n')
    links = []
    for record in records:
        write(f'programs/{record["id"]}.html', program_page(record, evidence, base_url))
        write(f'data/programs/{record["id"]}.json', json.dumps(record, indent=2, ensure_ascii=False) + '\n')
        write(f'data/reports/{record["id"]}.json', json.dumps(bts.completeness(record), indent=2, ensure_ascii=False) + '\n')
        links.append(f'<li><a href="programs/{record["id"]}.html">{html.escape(confirmed(record, "program_title"))}'
                     f' — {html.escape(confirmed(record, "qualification"))}</a><p>Review: {record["review_status"]}; '
                     f'checked {record["verification_date"]}</p></li>')
    for key, src in evidence.items():
        write(f'data/evidence/{key}.json', json.dumps(src, indent=2, ensure_ascii=False) + '\n')
    write('index.html', page('University program research directories', '<h1>University program research directories</h1>'
          '<p>Three independently researched records for testing URL-based import compatibility. '
          'All records await human review. Compatibility has not been demonstrated.</p>'
          '<h2>Oxford pilot programs</h2><ul class="programs">' + ''.join(links) + '</ul>'
          '<p><a href="programs/cambridge/undergraduate/index.html">Cambridge undergraduate workbook research</a></p>'
          '<p><a href="programs/imperial/undergraduate/index.html">Imperial undergraduate 2027 research directory</a></p>'
          '<p><a href="data/programs.csv">Download all records (CSV)</a></p>',
          canonical=base_url.rstrip('/') + '/' if base_url else None))
    write('data/programs.csv', export_csv(records))
    write('assets/style.css', (root / 'templates/style.css').read_text(encoding='utf-8'))
    write('.nojekyll', '')
    if cambridge_records:
        cambridge.build(root, out, base_url)
    imperial.build(root, out, base_url)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'build'])
    parser.add_argument('--base-url', default='', help='e.g. https://OWNER.github.io/bts-university-program-data')
    args = parser.parse_args()
    if args.command == 'validate':
        records, _ = load()
        cambridge_report = cambridge.validate()
        imperial_catalog = imperial.validate()
        print(f'Validated {len(records)} Oxford records; {cambridge_report.get("record_count", 0)} '
              f'Cambridge research records; {imperial_catalog["record_count"]} Imperial research records.')
    else:
        print(f'Built {build(base_url=args.base_url)}')


if __name__ == '__main__':
    main()
