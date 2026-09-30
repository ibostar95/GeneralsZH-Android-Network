#!/usr/bin/env python3
"""Summarize the dedicated Generals nginx JSON log without collecting client IDs.

Counts HTTP file transfers, not verified installations of the complete game.
Accepts several log files so rotated logs can be included in the report.
"""

import argparse
import gzip
import json
from pathlib import Path


def empty_counters():
    return {
        "file_requests": 0,
        "full_file_responses": 0,
        "range_responses": 0,
        "incomplete_responses": 0,
        "error_responses": 0,
        "transferred_bytes": 0,
    }


def summarize(lines):
    report = {"totals": empty_counters(), "days": {}, "files": {}, "invalid_lines": 0}
    for line in lines:
        try:
            event = json.loads(line)
            if event.get("method") != "GET" or not event.get("uri", "").lower().endswith(".big"):
                continue
            status = int(event["status"])
            sent = int(event["bytes"])
            date = event["time"][:10]
            uri = event["uri"]
            if sent < 0 or len(date) != 10:
                raise ValueError("Invalid log record")
        except (ValueError, TypeError, KeyError, AttributeError):
            report["invalid_lines"] += 1
            continue

        counters = [
            report["totals"],
            report["days"].setdefault(date, empty_counters()),
            report["files"].setdefault(uri, empty_counters()),
        ]
        for item in counters:
            item["file_requests"] += 1
            if status in (200, 206):
                item["transferred_bytes"] += sent
                if event.get("completed") != "OK":
                    item["incomplete_responses"] += 1
                elif status == 200:
                    item["full_file_responses"] += 1
                else:
                    item["range_responses"] += 1
            else:
                item["error_responses"] += 1
    return report


def read_logs(paths):
    for path in paths:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as stream:
            yield from stream


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, help="Optional local report JSON path")
    args = parser.parse_args()
    report = summarize(read_logs(args.logs))
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
