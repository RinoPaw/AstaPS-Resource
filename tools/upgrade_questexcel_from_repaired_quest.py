#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

# Loading the Chapter 1207 module loads the cumulative prerequisite chain through 1207.
import fix_chapter1207_prerequisites  # noqa: F401
import fix_liyue_prerequisites as cumulative
import fix_chapter1104_quest_rows as chapter1104
import fix_chapter1206_quest_rows as chapter1206
import fix_early_quest_fields as early

DEFAULT_PATH = Path("ExcelBinOutput/QuestExcelConfigData.json")
EXPECTED_ROW_COUNT = 33217
EXPECTED_CUMULATIVE_REPAIRS = 678
EXPECTED_SPECIAL_REPAIRS = 95

AMBER_FINISH_EXEC = [
    {
        "param": ["1"],
        "type": "QUEST_EXEC_GRANT_TRIAL_AVATAR",
    }
]


def render_object(obj: dict) -> str:
    raw = json.dumps(obj, ensure_ascii=False, indent=2)
    lines = raw.splitlines()
    return lines[0] + "\n" + "\n".join("  " + line for line in lines[1:])


def meaningful_execs(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict) and entry.get("type")]


def normalized_execs(value) -> list[dict]:
    return [
        {"type": entry.get("type"), "param": entry.get("param", [])}
        for entry in meaningful_execs(value)
    ]


def accept_key(entry: dict):
    if not isinstance(entry, dict) or not entry.get("type"):
        return None
    params = entry.get("param", [])
    if not isinstance(params, list):
        params = []
    if entry.get("type") in ("QUEST_COND_STATE_EQUAL", "QUEST_COND_STATE_NOT_EQUAL") and len(params) >= 2:
        params = params[:2]
    return (
        entry.get("type"),
        tuple(params),
        entry.get("param_str", entry.get("paramStr", "")) or "",
    )


def exec_key(entry: dict):
    if not isinstance(entry, dict) or not entry.get("type"):
        return None
    params = entry.get("param", [])
    if not isinstance(params, list):
        params = []
    return entry.get("type"), tuple(params)


def merge_entries_preserving_existing(current, expected, key_fn) -> list[dict]:
    """Keep every upstream entry and append only missing expected occurrences."""
    merged = list(current) if isinstance(current, list) else []
    counts = Counter(
        key for entry in merged if (key := key_fn(entry)) is not None
    )
    required = Counter()

    for entry in expected:
        key = key_fn(entry)
        if key is None:
            continue
        required[key] += 1
        if counts[key] < required[key]:
            merged.append(dict(entry))
            counts[key] += 1

    return merged


def raw_entry_key(entry) -> str:
    return json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_monotonic_field(before: dict, after: dict, field: str) -> None:
    before_entries = before.get(field)
    after_entries = after.get(field)
    before_entries = before_entries if isinstance(before_entries, list) else []
    after_entries = after_entries if isinstance(after_entries, list) else []

    before_counts = Counter(raw_entry_key(entry) for entry in before_entries)
    after_counts = Counter(raw_entry_key(entry) for entry in after_entries)
    removed = before_counts - after_counts
    if removed:
        raise ValueError(
            f"Quest {after.get('subId')} removed upstream {field} entries: {dict(removed)!r}"
        )


def assert_monotonic_quest_fields(before: dict, after: dict) -> None:
    assert_monotonic_field(before, after, "acceptCond")
    assert_monotonic_field(before, after, "beginExec")


def build_repairs():
    if len(cumulative.REPAIRS) != EXPECTED_CUMULATIVE_REPAIRS:
        raise SystemExit(
            f"Expected {EXPECTED_CUMULATIVE_REPAIRS} cumulative repairs, got {len(cumulative.REPAIRS)}"
        )

    special = tuple(chapter1104.CHAPTER_1104_REPAIRS) + tuple(chapter1206.CHAPTER_1206_REPAIRS)
    if len(special) != EXPECTED_SPECIAL_REPAIRS:
        raise SystemExit(
            f"Expected {EXPECTED_SPECIAL_REPAIRS} special repaired rows, got {len(special)}"
        )

    repairs = tuple(cumulative.REPAIRS) + special
    by_sub_id = {}
    for repair in repairs:
        if repair.sub_id in by_sub_id:
            raise SystemExit(f"Duplicate repair subId {repair.sub_id}")
        by_sub_id[repair.sub_id] = repair
    return by_sub_id


def patch_record(obj: dict, repair_by_sub_id: dict) -> list[str]:
    sub_id = int(obj.get("subId") or 0)
    changes: list[str] = []

    repair = repair_by_sub_id.get(sub_id)
    if repair is not None:
        if int(obj.get("mainId") or 0) != repair.main_id:
            raise ValueError(
                f"Quest {sub_id} has mainId={obj.get('mainId')}; expected {repair.main_id}"
            )

        expected_accept = [dict(entry) for entry in repair.expected_accept]
        merged_accept = merge_entries_preserving_existing(
            obj.get("acceptCond"), expected_accept, accept_key
        )
        if obj.get("acceptCond") != merged_accept:
            added = len(merged_accept) - len(obj.get("acceptCond") or [])
            obj["acceptCond"] = merged_accept
            changes.append(f"acceptCond+{added}")

        if repair.expected_comb is not None and obj.get("acceptCondComb") != repair.expected_comb:
            obj["acceptCondComb"] = repair.expected_comb
            changes.append(f"acceptCondComb={repair.expected_comb}")

    expected_accept = early.EXPECTED_ACCEPT.get(sub_id)
    if expected_accept is not None:
        merged_accept = merge_entries_preserving_existing(
            obj.get("acceptCond"), expected_accept, accept_key
        )
        if obj.get("acceptCond") != merged_accept:
            added = len(merged_accept) - len(obj.get("acceptCond") or [])
            obj["acceptCond"] = merged_accept
            changes.append(f"early.acceptCond+{added}")

    expected_begin = early.EXPECTED_BEGIN_EXECS.get(sub_id)
    if expected_begin is not None:
        merged_begin = merge_entries_preserving_existing(
            obj.get("beginExec"), expected_begin, exec_key
        )
        if obj.get("beginExec") != merged_begin:
            added = len(merged_begin) - len(obj.get("beginExec") or [])
            obj["beginExec"] = merged_begin
            changes.append(f"beginExec+{added}")

    for field, expected in early.EXPECTED_LOGIC.get(sub_id, {}).items():
        if obj.get(field) != expected:
            current = obj.get(field)
            if current not in (None, "", "LOGIC_NONE"):
                raise ValueError(
                    f"Quest {sub_id} has unexpected {field}={current!r}; expected {expected!r}"
                )
            obj[field] = expected
            changes.append(f"{field}={expected}")

    if sub_id == 35301:
        current = normalized_execs(obj.get("finishExec"))
        expected = normalized_execs(AMBER_FINISH_EXEC)
        if current != expected:
            if current:
                raise ValueError(
                    f"Quest 35301 has unexpected meaningful finishExec={current!r}; expected {expected!r}"
                )
            obj["finishExec"] = [dict(entry) for entry in AMBER_FINISH_EXEC]
            changes.append("finishExec=QUEST_EXEC_GRANT_TRIAL_AVATAR")

    return changes


def validate_population(root: list) -> None:
    if len(root) != EXPECTED_ROW_COUNT:
        raise SystemExit(f"Expected {EXPECTED_ROW_COUNT} QuestExcel rows, got {len(root)}")

    ids = [int(row.get("subId") or 0) for row in root if isinstance(row, dict)]
    if len(ids) != EXPECTED_ROW_COUNT:
        raise SystemExit("QuestExcel contains non-object rows")
    if len(set(ids)) != EXPECTED_ROW_COUNT:
        raise SystemExit("QuestExcel contains duplicate subId rows")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Overlay evidence-backed Rino quest repairs onto the complete upstream 33,217-row "
            "QuestExcel population without replacing untouched upstream rows."
        )
    )
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    path: Path = args.path
    text = path.read_text(encoding="utf-8")
    root = json.loads(text)
    if not isinstance(root, list):
        raise SystemExit(f"{path} must contain a top-level JSON array")
    validate_population(root)

    repair_by_sub_id = build_repairs()
    wanted = set(repair_by_sub_id) | set(early.TARGETS) | {35301}
    found: set[int] = set()
    replacements: list[tuple[int, int, str]] = []
    changed_rows = 0

    for start, end in early.iter_top_level_objects(text):
        raw = text[start:end]
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            continue
        sub_id = int(obj.get("subId") or 0)
        if sub_id not in wanted:
            continue
        if sub_id in found:
            raise SystemExit(f"Quest {sub_id} appears more than once")
        found.add(sub_id)

        before = json.loads(raw)
        changes = patch_record(obj, repair_by_sub_id)
        assert_monotonic_quest_fields(before, obj)
        if changes:
            changed_rows += 1
            replacements.append((start, end, render_object(obj)))
            print(f"Quest {sub_id}: " + ", ".join(changes))

    missing = sorted(wanted - found)
    if missing:
        raise SystemExit(f"Expected repaired QuestExcel rows not found: {missing}")

    if args.check:
        if replacements:
            print(f"Pending QuestExcel overlay rows: {changed_rows}")
            return 1
        print("QuestExcel population and audited overlays are already current.")
        return 0

    if replacements:
        patched_text = text
        for start, end, patched in reversed(replacements):
            patched_text = patched_text[:start] + patched + patched_text[end:]

        parsed = json.loads(patched_text)
        if not isinstance(parsed, list):
            raise SystemExit("Patched QuestExcel stopped being a JSON array")
        validate_population(parsed)

        probe_by_id = {
            int(row.get("subId") or 0): row
            for row in parsed
            if isinstance(row, dict) and int(row.get("subId") or 0) in wanted
        }
        for sub_id in sorted(wanted):
            probe = dict(probe_by_id[sub_id])
            if patch_record(probe, repair_by_sub_id):
                raise SystemExit(f"Quest {sub_id} failed post-write semantic validation")

        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(patched_text, encoding="utf-8", newline="")
        os.replace(tmp, path)
        print(f"Updated: {path}")
        print(f"Repaired QuestExcel rows: {changed_rows}")
    else:
        print("Nothing to do; QuestExcel overlay is already current.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
