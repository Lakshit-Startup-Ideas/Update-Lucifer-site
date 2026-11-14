import copy
import json
import unittest
from pathlib import Path

from check_append_only import check

BASE = {"schema": 1, "rule": "r", "versions": [{"id": "V1"}], "entries": [
    {"id": "a", "version": "V1", "label": "L", "date": "2026-01-01", "title": "t", "status": "done", "summary": "s", "points": ["p"], "not_shown": [], "links": [], "updates": []}]}


def grown():
    cur = copy.deepcopy(BASE)
    cur["versions"].append({"id": "V2"})
    cur["entries"].append({**copy.deepcopy(BASE["entries"][0]), "id": "b", "version": "V2"})
    return cur


class AppendOnly(unittest.TestCase):
    def test_unchanged_and_grown_are_fine(self):
        self.assertEqual(check(BASE, copy.deepcopy(BASE)), [])
        self.assertEqual(check(BASE, grown()), [])
        self.assertEqual(check(None, grown()), [])

    def test_an_update_may_be_appended_but_not_edited(self):
        cur = copy.deepcopy(BASE)
        cur["entries"][0]["updates"] = [{"date": "2026-02-01", "text": "confirmed"}]
        self.assertEqual(check(BASE, cur), [])
        later = copy.deepcopy(cur)
        later["entries"][0]["updates"].append({"date": "2026-03-01", "text": "more"})
        self.assertEqual(check(cur, later), [])
        edited = copy.deepcopy(later)
        edited["entries"][0]["updates"][0]["text"] = "changed"
        self.assertTrue(any("update" in p for p in check(later, edited)))
        dropped = copy.deepcopy(later)
        dropped["entries"][0]["updates"] = dropped["entries"][0]["updates"][1:]
        self.assertTrue(check(later, dropped))

    def test_editing_a_published_field_is_refused(self):
        for field, value in (("title", "new"), ("summary", "new"), ("points", []), ("date", "2027-01-01"), ("status", "partly"), ("links", [{"label": "x", "href": "y"}])):
            cur = copy.deepcopy(BASE)
            cur["entries"][0][field] = value
            self.assertTrue(any("edited" in p for p in check(BASE, cur)), field)

    def test_removing_or_reordering_is_refused(self):
        self.assertTrue(any("removed" in p for p in check(grown(), copy.deepcopy(BASE))))
        cur = grown()
        cur["entries"].reverse()
        self.assertTrue(any("order" in p for p in check(grown(), cur)))
        gone = grown()
        del gone["versions"][0]
        self.assertTrue(any("version block" in p for p in check(grown(), gone)))

    def test_schema_rule_ids_and_required_fields(self):
        cur = copy.deepcopy(BASE)
        cur["rule"] = "other"
        self.assertTrue(any("rule changed" in p for p in check(BASE, cur)))
        dup = grown()
        dup["entries"][1]["id"] = "a"
        self.assertTrue(any("duplicate" in p for p in check(BASE, dup)))
        bad = grown()
        del bad["entries"][1]["summary"]
        bad["entries"][1]["status"] = "weird"
        bad["entries"][1]["version"] = "V9"
        problems = check(BASE, bad)
        self.assertTrue(any("missing" in p for p in problems) and any("status" in p for p in problems) and any("not declared" in p for p in problems))

    def test_the_real_file_passes_against_itself(self):
        current = json.loads((Path(__file__).resolve().parent.parent / "data" / "milestones.json").read_text())
        self.assertEqual(check(current, current), [])


if __name__ == "__main__":
    unittest.main()
