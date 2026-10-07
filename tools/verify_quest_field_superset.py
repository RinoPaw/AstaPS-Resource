#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

FIELDS = ("acceptCond", "beginExec")


def load_rows(path: Path) -> dict[int, dict]:
    root = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(root, list):
        raise SystemExit(f"{path} must contain a top-level JSON array")

    rows: dict[int, dict] = {}
    for row in root:
        if not isinstance(row, dict):
            raise SystemExit(f"{path} contains a non-object row")
        sub_id = int(row.get("subId") or 0)
        if sub_id <= 0:
            raise SystemExit(f"{path} contains an invalid subId: {row.get('subId')!r}")
        if sub_id in rows:
            raise SystemExit(f"{path} contains duplicate subId {sub_id}")
        rows[sub_id] = row
    return rows


def entries(row: dict, field: str) -> list:
    value = row.get(field)
    return value if isinstance(value, list) else []


def entry_key(entry) -> str:
    return json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def field_counter(row: dict, field: str) -> Counter[str]:
    return Counter(entry_key(entry) for entry in entries(row, field))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that current QuestExcel acceptCond and beginExec are a strict superset "
            "of an upstream QuestExcel baseline. Existing upstream entries, including duplicate "
            "occurrences and converter placeholders, may not be removed."
        )
    )
    parser.add_argument("upstream", type=Path)
    parser.add_argument("current", type=Path)
    args = parser.parse_args()

    upstream = load_rows(args.upstream)
    current = load_rows(args.current)

    missing_rows = sorted(set(upstream) - set(current))
    if missing_rows:
        print(f"Missing upstream quest rows: {len(missing_rows)}")
        print("First missing subIds:", missing_rows[:50])
        return 1

    failures: list[tuple[int, str, dict[str, int]]] = []
    added_counts = {field: 0 for field in FIELDS}
    extended_rows = {field: 0 for field in FIELDS}

    for sub_id, before in upstream.items():
        after = current[sub_id]
        for field in FIELDS:
            before_counts = field_counter(before, field)
            after_counts = field_counter(after, field)
            removed = before_counts - after_counts
            if removed:
                failures.append((sub_id, field, dict(removed)))
                continue

            added = after_counts - before_counts
            if added:
                extended_rows[field] += 1
                added_counts[field] += sum(added.values())

    if failures:
        print(
            f"Quest field superset check FAILED: {len(failures)} "
            "subId/field pairs removed upstream entries."
        )
        for sub_id, field, removed in failures[:100]:
            print(f"Quest {sub_id} {field}: removed {removed!r}")
        if len(failures) > 100:
            print(f"... {len(failures) - 100} more failures omitted")
        return 1

    print(f"Upstream rows checked: {len(upstream)}")
    print(f"Current rows: {len(current)}")
    for field in FIELDS:
        print(
            f"{field}: upstream preserved; "
            f"{added_counts[field]} added entries across {extended_rows[field]} rows"
        )
    print("Quest field superset check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
