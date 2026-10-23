"""Fixture-only tests for the Blossom Lua source-coverage audit."""
import json
import tempfile
import unittest
from pathlib import Path
from audit_blossom_lua_71 import audit, inspect_script


class BlossomLuaAuditTest(unittest.TestCase):
    def test_blue_generated_and_missing_are_reported_without_fabricating_gold(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"id": 504018001, "cityId": 5, "limit_level": 8,
                 "sectionId": 4018, "refreshTypeVec": [1, 3], "newGroupVec": [133412176]},
                {"id": 504018002, "cityId": 5, "limit_level": 12,
                 "sectionId": 4018, "refreshTypeVec": [1, 3], "newGroupVec": [133412177]},
                {"id": 504018003, "cityId": 5, "limit_level": 28,
                 "sectionId": 4018, "refreshTypeVec": [1, 3], "newGroupVec": [133412178]},
                {"id": 504018004, "cityId": 5, "limit_level": 8,
                 "sectionId": 4018, "refreshTypeVec": [10], "newGroupVec": [133412179]},
            ]
            path = root / "ExcelBinOutput" / "BlossomGroupsExcelConfigData.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(rows), encoding="utf-8")
            lua = root / "Scripts/Scene/3/scene3_group133412176.lua"
            lua.parent.mkdir(parents=True)
            lua.write_text("-- Auto-generated spawn data\n"
                           "gadgets = {{config_id=1, gadget_id = 70360057}}\n"
                           "-- gadget_id = 70360056\n", encoding="utf-8")
            report = audit(root, 5, 18, 3)
            self.assertEqual({"eligibleCamps": 2, "referencedGroups": 2,
                              "missingGroups": 1, "presentGroups": 1,
                              "generatedGroups": 1, "blueGroups": 1, "goldGroups": 0},
                             report["summary"])
            self.assertFalse(report["originalClientVerified"])
            self.assertEqual(["blue"], report["camps"][0]["groups"][0]["kinds"])
            self.assertEqual("missing", report["camps"][1]["groups"][0]["status"])

    def test_finds_gold_and_blue_and_distinguishes_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            lua = Path(directory) / "example.lua"
            lua.write_text("gadgets={{gadget_id=70360056},{gadget_id=70360057}}",
                           encoding="utf-8")
            self.assertEqual({"status": "present", "kinds": ["blue", "gold"],
                              "generated": False}, inspect_script(lua))
            self.assertEqual({"status": "missing", "kinds": [], "generated": False},
                             inspect_script(lua.with_suffix(".missing")))


if __name__ == "__main__":
    unittest.main()
