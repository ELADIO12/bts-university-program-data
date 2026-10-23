"""Cambridge workbook intake, separation, and static publishing checks."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import bts, cambridge, pipeline


ROOT = Path(__file__).resolve().parents[1]


class CambridgeResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.raw = cambridge.load(ROOT)

    def test_all_workbook_rows_and_bts_fields_are_mapped(self):
        self.assertEqual(len(self.records), 32)
        self.assertEqual({r["source_workbook"]["row"] for r in self.records}, set(range(2, 34)))
        self.assertEqual(len(self.raw["sheets"]), 3)
        for record in self.records:
            self.assertEqual(set(record["bts_fields"]), set(bts.LABELS))
            self.assertEqual(record["university"]["bts_university_id"], 92862)
            self.assertEqual(record["university"]["name"], "University of Cambridge")
            self.assertEqual(record["source_workbook"]["sha256"], self.raw["sha256"])
        self.assertEqual(cambridge.validate(ROOT)["record_count"], 32)

    def test_workbook_values_do_not_become_verified_facts(self):
        for record in self.records:
            self.assertEqual(record["language_classification"], "UNVERIFIED_LANGUAGE")
            self.assertEqual(record["existing_bts_match"], "unknown")
            self.assertEqual(record["import_eligibility"], "hold")
            self.assertEqual(record["human_review_status"], "pending")
            self.assertTrue(all(field["status"] != "verified" for field in record["bts_fields"].values()))
            self.assertTrue(all(field["value"] is None for field in record["bts_fields"].values() if field["status"] == "unverified"))
        summary = cambridge.summary(self.records)
        self.assertEqual(summary["new_import_ready"], 0)
        self.assertEqual(summary["language_review_required"], 32)
        self.assertEqual(summary["duplicate_check_pending"], 32)
        self.assertEqual(summary["workbook_direct_course_links"], 3)
        self.assertEqual(summary["workbook_explicit_exclusions"], 1)

    def test_identity_duplicates_and_fee_scope(self):
        self.assertEqual(len({r["id"] for r in self.records}), 32)
        self.assertEqual(len({(r["program"]["title"].casefold(), r["program"]["qualification"].casefold())
                              for r in self.records}), 32)
        for record in self.records:
            row, _ = cambridge._row(self.raw, record["source_workbook"]["row"])
            self.assertEqual(record["program"]["title"], row["Program Title"])
            self.assertEqual(record["program"]["qualification"], row["Degree Type"])
            tuition = record["bts_fields"]["tuition_non_eu"]["value"]
            if row["Tuition (non-EU/yr GBP)"] is None:
                self.assertIsNone(tuition)
            else:
                self.assertEqual(tuition["amount"], row["Tuition (non-EU/yr GBP)"])
                self.assertEqual(tuition["period"], "year")
                self.assertEqual(tuition["currency"], "GBP")
                self.assertIsNone(tuition["academic_year"])
            duration = record["bts_fields"]["duration_original"]["value"]
            self.assertEqual(duration["amount"], row["Exact Duration (years)"])
        self.assertEqual(cambridge.summary(self.records)["overseas_fee_missing_in_workbook"], 1)

    def test_aggregate_csv_and_exclusions_cover_same_32_records(self):
        target = ROOT / cambridge.DATA
        aggregate = json.loads((target / "cambridge-undergraduate.json").read_text(encoding="utf-8"))
        excluded = json.loads((target / "excluded-programs.json").read_text(encoding="utf-8"))
        manifest = json.loads((target / "discovery-manifest.json").read_text(encoding="utf-8"))
        with (target / "cambridge-undergraduate.csv").open(encoding="utf-8", newline="") as stream:
            csv_rows = list(csv.DictReader(stream))
        ids = {r["id"] for r in self.records}
        self.assertEqual({r["id"] for r in aggregate["records"]}, ids)
        self.assertEqual({r["id"] for r in excluded}, ids)
        self.assertEqual({r["id"] for r in manifest["programs"]}, ids)
        self.assertEqual({r["id"] for r in csv_rows}, ids)

    def test_site_has_32_research_pages_and_empty_ready_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            for name in ("data", "schema", "templates"):
                shutil.copytree(ROOT / name, temp_root / name)
            site = pipeline.build(temp_root, "https://example.github.io/bts-university-program-data")
            index = (site / cambridge.COLLECTION / "index.html").read_text(encoding="utf-8")
            ready = (site / cambridge.COLLECTION / "import-ready/index.html").read_text(encoding="utf-8")
            for record in self.records:
                page = site / cambridge.COLLECTION / cambridge.filename(record)
                self.assertTrue(page.is_file())
                self.assertIn(cambridge.filename(record), index)
                self.assertIn("UNVERIFIED_LANGUAGE", page.read_text(encoding="utf-8"))
                self.assertNotIn(cambridge.filename(record), ready)
            self.assertIn("No programs currently qualify", ready)
            for oxford in ("oxford-archaeology-and-anthropology-ba",
                           "oxford-classical-archaeology-and-ancient-history-ba",
                           "oxford-archaeological-science-msc"):
                self.assertTrue((site / "programs" / (oxford + ".html")).is_file())


if __name__ == "__main__":
    unittest.main()
