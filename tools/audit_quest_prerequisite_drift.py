#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_QUEST_EXCEL = Path("ExcelBinOutput/QuestExcelConfigData.json")
DEFAULT_CHAPTER_EXCEL = Path("ExcelBinOutput/ChapterExcelConfigData.json")

STATE_EQUAL = "QUEST_COND_STATE_EQUAL"
STATE_NOT_EQUAL = "QUEST_COND_STATE_NOT_EQUAL"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def meaningful_conditions(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict) and entry.get("type")]


def normalize_condition(entry: dict) -> dict:
    params = entry.get("param", [])
    if not isinstance(params, list):
        params = []
    if entry.get("type") in (STATE_EQUAL, STATE_NOT_EQUAL) and len(params) >= 2:
        params = params[:2]
    return {
        "type": entry.get("type"),
        "param": params,
        "param_str": entry.get("param_str", entry.get("paramStr", "")) or "",
    }


def normalize_accept(value) -> list[dict]:
    return [normalize_condition(entry) for entry in meaningful_conditions(value)]


def normalize_comb(row: dict) -> str:
    value = row.get("acceptCondComb")
    return value if value not in (None, "", "LOGIC_NONE") else "LOGIC_AND"


def iter_subquests(document) -> Iterable[dict]:
    if isinstance(document, dict):
        subquests = document.get("subQuests")
        if isinstance(subquests, list):
            yield from (row for row in subquests if isinstance(row, dict))
        return
    if isinstance(document, list):
        yield from (row for row in document if isinstance(row, dict))


def chapter_begin_ids(path: Path) -> set[int]:
    if not path.is_file():
        return set()
    root = load_json(path)
    if not isinstance(root, list):
        raise ValueError(f"{path} must contain a top-level JSON array")
    return {
        int(row.get("beginQuestId"))
        for row in root
        if isinstance(row, dict) and isinstance(row.get("beginQuestId"), int) and row.get("beginQuestId") > 0
    }


def reference_file(root: Path, json_file: str, main_id: int) -> Path | None:
    candidates = []
    if json_file:
        candidates.append(root / Path(json_file).name)
    if main_id:
        candidates.append(root / f"{main_id}.json")
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_reference_row(root: Path, json_file: str, main_id: int, sub_id: int) -> tuple[dict | None, str | None]:
    path = reference_file(root, json_file, main_id)
    if path is None:
        return None, None
    try:
        document = load_json(path)
    except (OSError, json.JSONDecodeError):
        return None, str(path)
    for row in iter_subquests(document):
        if int(row.get("subId") or 0) == sub_id:
            return row, str(path)
    return None, str(path)


def is_zero_finished(conditions: list[dict]) -> bool:
    if len(conditions) != 1:
        return False
    cond = conditions[0]
    return cond.get("type") == STATE_EQUAL and cond.get("param") == [0, 3]


def classify(current: list[dict], current_comb: str, reference: list[dict], reference_comb: str) -> str:
    if current == reference and current_comb == reference_comb:
        return "match"
    if is_zero_finished(current) and reference:
        return "zeroed-predecessor"
    if not current and reference:
        return "missing-accept"
    if len(current) < len(reference):
        return "conditions-lost"
    if len(current) > len(reference):
        return "conditions-added"
    if current_comb != reference_comb:
        return "combiner-drift"
    if len(current) == 1 and len(reference) == 1:
        cur = current[0]
        ref = reference[0]
        if cur.get("type") == ref.get("type") == STATE_EQUAL:
            cp = cur.get("param", [])
            rp = ref.get("param", [])
            if len(cp) >= 2 and len(rp) >= 2 and cp[1] == rp[1] and cp[0] != rp[0]:
                return "predecessor-drift"
    return "condition-drift"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the flattened 7.1 quest prerequisite graph with an intact historical "
            "BinOutput/Quest tree. Reports all acceptCond/acceptCondComb drift; never writes resources."
        )
    )
    parser.add_argument("quest_excel", nargs="?", type=Path, default=DEFAULT_QUEST_EXCEL)
    parser.add_argument("--reference-bin-root", type=Path, required=True)
    parser.add_argument("--chapter-excel", type=Path, default=DEFAULT_CHAPTER_EXCEL)
    parser.add_argument("--main", type=int, default=None, help="Limit output to one main quest id.")
    parser.add_argument("--only-differences", action="store_true")
    parser.add_argument("--json", dest="json_output", type=Path, default=None)
    args = parser.parse_args()

    root = load_json(args.quest_excel)
    if not isinstance(root, list):
        raise SystemExit(f"{args.quest_excel} must contain a top-level JSON array")

    chapter_begins = chapter_begin_ids(args.chapter_excel)
    counts: Counter[str] = Counter()
    report: list[dict] = []
    missing_reference = 0

    for row in root:
        if not isinstance(row, dict):
            continue
        main_id = int(row.get("mainId") or 0)
        sub_id = int(row.get("subId") or 0)
        if args.main is not None and main_id != args.main:
            continue

        json_file = str(row.get("json_file") or "")
        reference_row, source = load_reference_row(
            args.reference_bin_root, json_file, main_id, sub_id
        )
        if reference_row is None:
            missing_reference += 1
            continue

        current_accept = normalize_accept(row.get("acceptCond"))
        reference_accept = normalize_accept(reference_row.get("acceptCond"))
        current_comb = normalize_comb(row)
        reference_comb = normalize_comb(reference_row)
        kind = classify(current_accept, current_comb, reference_accept, reference_comb)
        counts[kind] += 1

        if kind == "match" and args.only_differences:
            continue

        report.append(
            {
                "classification": kind,
                "json_file": json_file,
                "main_id": main_id,
                "sub_id": sub_id,
                "order": int(row.get("order") or 0),
                "show_type": str(row.get("showType") or ""),
                "chapter_begin": sub_id in chapter_begins,
                "current_accept": current_accept,
                "reference_accept": reference_accept,
                "current_comb": current_comb,
                "reference_comb": reference_comb,
                "reference_source": source,
            }
        )

    print("Quest prerequisite drift audit")
    print(f"  compared: {sum(counts.values())}")
    print(f"  reference-missing: {missing_reference}")
    for name in (
        "match",
        "zeroed-predecessor",
        "missing-accept",
        "predecessor-drift",
        "conditions-lost",
        "conditions-added",
        "combiner-drift",
        "condition-drift",
    ):
        print(f"  {name}: {counts[name]}")

    printable = [item for item in report if item["classification"] != "match"]
    if not args.only_differences:
        printable = report

    if printable:
        print()
        print("class\tmain\tsub\torder\tchapterBegin\tcurrent\treference\tcurrentComb\treferenceComb")
        for item in printable:
            print(
                "\t".join(
                    [
                        item["classification"],
                        str(item["main_id"]),
                        str(item["sub_id"]),
                        str(item["order"]),
                        "yes" if item["chapter_begin"] else "no",
                        json.dumps(item["current_accept"], ensure_ascii=False, separators=(",", ":")),
                        json.dumps(item["reference_accept"], ensure_ascii=False, separators=(",", ":")),
                        item["current_comb"],
                        item["reference_comb"],
                    ]
                )
            )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(
                {
                    "counts": dict(counts),
                    "reference_missing": missing_reference,
                    "rows": report,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print()
        print(f"Wrote JSON report: {args.json_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
