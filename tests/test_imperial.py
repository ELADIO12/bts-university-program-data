"""Imperial source-catalog integrity and static publishing checks."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import imperial, pipeline

ROOT = Path(__file__).resolve().parents[1]


class ImperialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = imperial.validate(ROOT)
        cls.records = cls.catalog["records"]

    def test_2027_directory_and_study_options_are_distinct(self):
        self.assertEqual(self.catalog["directory_listing_count"], 73)
        self.assertEqual(self.catalog["course_page_count"], 73)
        self.assertEqual(len(self.records), 116)
        self.assertEqual(sum(r["option_index"] == 0 for r in self.records), 73)
        self.assertEqual(sum(r["option_index"] > 0 for r in self.records), 43)
        self.assertEqual(len({r["id"] for r in self.records}), 116)
        self.assertEqual(len({r["source_url"] for r in self.records}), 73)
        self.assertTrue(all("/undergraduate/2027/" in r["source_url"] for r in self.records))

    def test_unsupported_facts_stay_unverified(self):
        for source in self.records:
            record = imperial.public_record(source, self.catalog["verification_date"])
            self.assertEqual(record["bts_import_eligibility"], "hold")
            self.assertEqual(record["review_status"], "human_review_pending")
            for key in ("language_of_instruction", "english_proficiency_requirements",
                        "academic_subject", "bts_university_slug"):
                self.assertIsNone(record["fields"][key]["value"])
                self.assertEqual(record["fields"][key]["status"], "unverified")
            for field in record["fields"].values():
                if field["value"] is not None:
                    self.assertEqual(field["status"], "official_page_observed")
                    self.assertEqual(field["source_url"], source["source_url"])
                    self.assertTrue(field["locator"])
            if source["option_index"]:
                self.assertIsNone(source["overseas_fee"])
        fees = [r["overseas_fee"] for r in self.records if r["overseas_fee"]]
        self.assertEqual(len(fees), 72)
        self.assertEqual(sum(fee["period"] is None for fee in fees), 2)
        self.assertTrue(all(fee["academic_year"] is None for fee in fees))

    def test_build_has_directory_all_pages_json_and_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("data", "schema", "templates"):
                shutil.copytree(ROOT / name, root / name)
            site = pipeline.build(root, "https://example.github.io/bts-university-program-data")
            directory = (site / imperial.COLLECTION / "index.html").read_text(encoding="utf-8")
            self.assertEqual(directory.count('class="notice"'), 1)
            self.assertIn("116 individual program", directory)
            with (site / imperial.DATA / "programs.csv").open(encoding="utf-8", newline="") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 116)
            for source in self.records:
                page = (site / imperial.COLLECTION / (source["id"] + ".html")).read_text(encoding="utf-8")
                record = json.loads((site / imperial.DATA / "programs" / (source["id"] + ".json"))
                                    .read_text(encoding="utf-8"))
                self.assertIn(source["id"] + ".html", directory)
                self.assertIn(source["source_url"], page)
                self.assertIn("human review pending", page)
                self.assertIn("Not verified", page)
                self.assertEqual(record["fields"]["program_title"]["value"], source["title"])
                script = page.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
                self.assertEqual(json.loads(script)["@type"], "Course")
                self.assertEqual(json.loads(script)["identifier"], source["id"])

    def test_duplicate_identity_and_option_fee_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "data/imperial").mkdir(parents=True)
            (root / "schema").mkdir()
            shutil.copy(ROOT / imperial.SCHEMA, root / imperial.SCHEMA)
            path = root / imperial.SOURCE
            catalog = json.loads(json.dumps(self.catalog))
            catalog["records"][1]["title"] = catalog["records"][0]["title"]
            catalog["records"][1]["qualification"] = catalog["records"][0]["qualification"]
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate Imperial program identity"):
                imperial.validate(root)
            catalog = json.loads(json.dumps(self.catalog))
            catalog["records"][1]["overseas_fee"] = catalog["records"][0]["overseas_fee"]
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Study-option fee"):
                imperial.validate(root)


if __name__ == "__main__":
    unittest.main()
