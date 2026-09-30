import importlib.util
import gzip
import json
import tempfile
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location("stats", Path(__file__).with_name("generals-data-stats.py"))
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


def event(status=200, sent=100, completed="OK", method="GET", uri="/data/zh-INIZH.big"):
    return json.dumps({"time": "2026-09-30T19:00:00+05:00", "method": method,
                       "uri": uri, "status": status, "bytes": sent, "completed": completed})


class TransferStatsTests(unittest.TestCase):
    def test_range_and_incomplete_responses_are_not_full_downloads(self):
        report = stats.summarize([event(), event(206, 40), event(sent=20, completed="")])
        self.assertEqual(report["totals"], {
            "file_requests": 3, "full_file_responses": 1, "range_responses": 1,
            "incomplete_responses": 1, "error_responses": 0, "transferred_bytes": 160,
        })
        self.assertEqual(report["days"]["2026-09-30"], report["totals"])
        self.assertEqual(report["files"]["/data/zh-INIZH.big"], report["totals"])

    def test_head_manifest_and_errors_do_not_inflate_file_downloads(self):
        report = stats.summarize([event(method="HEAD"), event(uri="/data/game-data-manifest.json"),
                                  event(404, 156), event(503, 100)])
        self.assertEqual(report["totals"]["file_requests"], 2)
        self.assertEqual(report["totals"]["full_file_responses"], 0)
        self.assertEqual(report["totals"]["transferred_bytes"], 0)
        self.assertEqual(report["totals"]["error_responses"], 2)

    def test_bad_log_lines_are_reported_without_losing_valid_events(self):
        report = stats.summarize(["broken", event(sent=-10), event()])
        self.assertEqual(report["invalid_lines"], 2)
        self.assertEqual(report["totals"]["file_requests"], 1)

    def test_plain_and_gzip_rotations_contribute_to_one_report(self):
        with tempfile.TemporaryDirectory() as folder:
            plain = Path(folder) / "downloads.jsonl"
            rotated = Path(folder) / "downloads.jsonl.2.gz"
            plain.write_text(event() + "\n", encoding="utf-8")
            with gzip.open(rotated, "wt", encoding="utf-8") as stream:
                stream.write(event(206, 40) + "\n")
            report = stats.summarize(stats.read_logs([plain, rotated]))
        self.assertEqual(report["totals"]["file_requests"], 2)
        self.assertEqual(report["totals"]["transferred_bytes"], 140)


if __name__ == "__main__":
    unittest.main()
