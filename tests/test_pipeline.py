import copy
import csv
import io
import json
import shutil
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from jsonschema.exceptions import ValidationError
from scripts import pipeline as p


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links, self.scripts, self.h1 = [], [], 0
        self.in_json = False
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if tag in ('a', 'link'):
            self.links.append(attrs.get('href', ''))
        if tag == 'script':
            self.in_json = attrs.get('type') == 'application/ld+json'
    def handle_data(self, value):
        if self.in_json:
            self.scripts.append(value)
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_json = False


class ValidationTests(unittest.TestCase):
    def setUp(self):
        records, self.evidence = p.load()
        self.records = copy.deepcopy(records)
        self.record = self.records[0]
    def check_bad(self):
        with self.assertRaises((ValueError, ValidationError)):
            p.validate(self.records, self.evidence)
    def test_three_pilot_records(self):
        self.assertEqual(len(self.records), 3)
        self.assertEqual(sum(p.confirmed(r, 'qualification') == 'MSc' for r in self.records), 1)
    def test_unknown_is_null(self):
        for record in self.records:
            self.assertIsNone(p.confirmed(record, 'bts_university_slug'))
            self.assertIsNone(p.confirmed(record, 'language_of_instruction'))
    def test_required_field(self):
        del self.record['fields']['duration']
        self.check_bad()
    def test_unexpected_field(self):
        self.record['approved_by_bts'] = True
        self.check_bad()
    def test_wrong_type(self):
        self.record['fields']['duration']['value']['amount'] = 'three'
        self.check_bad()
    def test_missing_evidence(self):
        self.record['fields']['program_title']['evidence'] = []
        self.check_bad()
    def test_dangling_evidence(self):
        self.record['fields']['program_title']['evidence'][0]['source_id'] = 'missing'
        self.check_bad()
    def test_non_official_evidence(self):
        next(iter(self.evidence.values()))['url'] = 'https://ox.ac.uk.example.com/course'
        self.check_bad()
    def test_blocked_evidence_cannot_confirm(self):
        for src in self.evidence.values():
            src['access_status'] = 'manual_evidence_required'
        self.check_bad()
    def test_unverified_cannot_contain_fact(self):
        self.record['fields']['language_of_instruction']['value'] = 'English'
        self.check_bad()
    def test_verified_cannot_be_null(self):
        self.record['fields']['study_mode']['value'] = None
        self.check_bad()
    def test_invalid_calendar_date(self):
        self.record['verification_date'] = '2026-02-30'
        self.check_bad()
    def test_future_date(self):
        self.record['verification_date'] = '2999-01-01'
        self.check_bad()
    def test_evidence_date_order(self):
        for src in self.evidence.values():
            src['accessed_on'] = '2999-01-01'
        self.check_bad()
    def test_bad_fee_year(self):
        self.record['fields']['international_tuition']['value']['academic_year'] = 'current'
        self.check_bad()
    def test_approval_claim_rejected(self):
        self.record['publication_status'] = 'approved'
        self.check_bad()
    def test_duplicate_id(self):
        self.records.append(copy.deepcopy(self.record))
        self.check_bad()
    def test_duplicate_identity_with_different_source(self):
        other = copy.deepcopy(self.record)
        other['id'] += '-copy'
        other['fields']['program_title']['value'] = '  '+p.confirmed(other, 'program_title').replace(' and ', ' & ').upper()+'! '
        other['fields']['source_url']['value'] += '/alternate'
        self.records.append(other)
        self.check_bad()
    def test_duplicate_source_with_changed_title(self):
        other = copy.deepcopy(self.record)
        other['id'] += '-copy'
        other['fields']['program_title']['value'] = 'Different spelling'
        other['fields']['source_url']['value'] += '/?tracking=1#overview'
        self.records.append(other)
        self.check_bad()
    def test_record_review_status(self):
        self.record['review_status'] = 'verified'
        self.check_bad()
    def test_manual_evidence_field_allowed(self):
        self.record['fields']['language_of_instruction']['status'] = 'manual_evidence_required'
        p.validate(self.records, self.evidence)
    def test_reject_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'bad.json'
            path.write_text('{"id":1,"id":2}', encoding='utf-8')
            with self.assertRaises(ValueError):
                p.read_json(path)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('data', 'schema', 'templates'):
            shutil.copytree(p.ROOT / directory, self.root / directory)
        self.records, self.evidence = p.load(self.root)
        self.base = 'https://example.github.io/bts-university-program-data'
        self.out = p.build(self.root, self.base)
    def test_links_resolve_under_repository_path(self):
        for file in self.out.rglob('*.html'):
            doc = Document(file.read_text(encoding='utf-8'))
            self.assertEqual(doc.h1, 1)
            for link in doc.links:
                if not urlsplit(link).scheme:
                    self.assertFalse(link.startswith('/'), link)
                    target = (file.parent / unquote(urlsplit(link).path)).resolve()
                    self.assertTrue(target.is_relative_to(self.out), link)
                    self.assertTrue(target.is_file(), link)
    def test_directory_links_all_programs(self):
        doc = Document((self.out/'index.html').read_text(encoding='utf-8'))
        for record in self.records:
            self.assertIn(f'programs/{record["id"]}.html', doc.links)
    def test_jsonld_and_provenance(self):
        for record in self.records:
            file = self.out/'programs'/(record['id']+'.html')
            text = file.read_text(encoding='utf-8')
            doc = Document(text)
            self.assertEqual(len(doc.scripts), 1)
            data = json.loads(doc.scripts[0])
            self.assertEqual(data['@type'], 'Course')
            self.assertEqual(data['about']['@type'], 'DefinedTerm')
            self.assertEqual(data['url'], self.base+'/programs/'+record['id']+'.html')
            self.assertEqual(data['isBasedOn'], p.confirmed(record, 'source_url'))
            self.assertNotIn('inLanguage', data)
            self.assertNotIn('offers', data)
            self.assertIn(p.NOTICE, text)
            self.assertIn('Human review pending', text)
            self.assertIn('2027-28', text)
            self.assertIn('Not verified', text)
    def test_json_source_copies(self):
        for record in self.records:
            self.assertEqual(p.read_json(self.out/'data/programs'/(record['id']+'.json')), record)
    def test_csv_roundtrip(self):
        rows = list(csv.DictReader(io.StringIO((self.out/'data/programs.csv').read_text(encoding='utf-8'))))
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row['language_of_instruction'], '')
            self.assertEqual(row['language_of_instruction_status'], 'unverified')
            self.assertEqual(json.loads(row['international_tuition'])['academic_year'], '2027-28')
            self.assertTrue(json.loads(row['program_title_provenance']))
    def test_html_and_jsonld_escape(self):
        record = copy.deepcopy(self.records[0])
        malicious = '</script><script>alert("x")</script> & <b>'
        record['fields']['summary']['value'] = malicious
        text = p.program_page(record, self.evidence, self.base)
        self.assertNotIn(malicious, text)
        self.assertIn('&lt;script&gt;', text)
        self.assertEqual(json.loads(Document(text).scripts[0])['description'], malicious)
    def test_csv_formula_escape(self):
        record = copy.deepcopy(self.records[0])
        record['fields']['summary']['value'] = '=HYPERLINK("https://example.com")'
        row = next(csv.DictReader(io.StringIO(p.export_csv([record]))))
        self.assertTrue(row['summary'].startswith("'="))
    def test_rebuild_is_deterministic_and_removes_stale(self):
        snapshot = {str(f.relative_to(self.out)):f.read_bytes() for f in self.out.rglob('*') if f.is_file()}
        stale = self.out/'programs/stale.html'
        stale.write_text('obsolete')
        p.build(self.root, self.base)
        self.assertFalse(stale.exists())
        self.assertEqual(snapshot, {str(f.relative_to(self.out)):f.read_bytes() for f in self.out.rglob('*') if f.is_file()})
    def test_invalid_base_url(self):
        with self.assertRaises(ValueError):
            p.build(self.root, 'javascript:alert(1)')
    def test_no_canonical_when_host_unknown(self):
        data = p.course_jsonld(self.records[0], '')
        self.assertNotIn('url', data)
    def test_fail_before_publishing_invalid_data(self):
        path = self.root/'data/programs'/(self.records[0]['id']+'.json')
        record = p.read_json(path)
        record['fields']['qualification']['value'] = None
        path.write_text(json.dumps(record), encoding='utf-8')
        with self.assertRaises((ValueError, ValidationError)):
            p.build(self.root, self.base)


if __name__ == '__main__':
    unittest.main()
