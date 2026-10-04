#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from fix_quest_prerequisites import REPAIRS, STATE_EQUAL


DEFAULT_REPORT = Path("audit-prerequisite-consensus-3700-4000.json")
PROLOGUE_MAIN_IDS = {
    306,
    307,
    308,
    309,
    311,
    351,
    352,
    353,
    354,
    355,
    356,
    357,
    358,
    359,
    360,
    361,
    362,
    363,
    370,
    371,
    372,
    373,
    374,
    375,
    376,
    377,
    20101,
    379,
    380,
    381,
    382,
    383,
    384,
    397,
    388,
    389,
    390,
    393,
    394,
    398,
    396,
    399,
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def is_simple_state_equal(row: dict) -> bool:
    reference = row.get("reference_accept")
    if not isinstance(reference, list) or len(reference) != 1:
        return False
    cond = reference[0]
    return (
        isinstance(cond, dict)
        and cond.get("type") == STATE_EQUAL
        and isinstance(cond.get("param"), list)
        and len(cond["param"]) >= 2
        and row.get("reference_comb") == "LOGIC_AND"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Filter a multi-reference quest prerequisite drift report down to unresolved Mondstadt "
            "Prologue rows with complete historical consensus. This command never edits resources."
        )
    )
    parser.add_argument("report", nargs="?", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--consensus-count",
        type=int,
        default=2,
        help="Required number of agreeing historical references (default: 2).",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        type=Path,
        default=None,
        help="Optional path for the filtered machine-readable report.",
    )
    args = parser.parse_args()

    root = load_json(args.report)
    if not isinstance(root, dict) or not isinstance(root.get("rows"), list):
        raise SystemExit(f"{args.report} is not a quest prerequisite drift JSON report")

    manifest_sub_ids = {repair.sub_id for repair in REPAIRS}
    prologue_rows = [
        row
        for row in root["rows"]
        if isinstance(row, dict) and int(row.get("main_id") or 0) in PROLOGUE_MAIN_IDS
    ]
    manifest_rows = [
        row for row in prologue_rows if int(row.get("sub_id") or 0) in manifest_sub_ids
    ]
    residual_rows = [
        row
        for row in prologue_rows
        if row.get("classification") != "match" and int(row.get("sub_id") or 0) not in manifest_sub_ids
    ]

    disagreements = [
        row for row in residual_rows if row.get("classification") == "reference-disagreement"
    ]
    partial = [
        row
        for row in residual_rows
        if row.get("classification") != "reference-disagreement"
        and (
            int(row.get("reference_consensus_count") or 0) != args.consensus_count
            or bool(row.get("missing_reference_roots"))
        )
    ]
    consensus = [
        row
        for row in residual_rows
        if row.get("classification") != "reference-disagreement"
        and int(row.get("reference_consensus_count") or 0) == args.consensus_count
        and not row.get("missing_reference_roots")
    ]

    simple = [row for row in consensus if is_simple_state_equal(row)]
    manual = [row for row in consensus if not is_simple_state_equal(row)]

    class_counts = Counter(str(row.get("classification") or "") for row in residual_rows)
    consensus_class_counts = Counter(str(row.get("classification") or "") for row in consensus)

    print("Mondstadt Prologue prerequisite consensus filter")
    print(f"  report: {args.report}")
    print(f"  Prologue rows in report: {len(prologue_rows)}")
    print(f"  manifest rows present/excluded: {len(manifest_rows)}")
    print(f"  residual differences: {len(residual_rows)}")
    print(f"  complete {args.consensus_count}-reference consensus: {len(consensus)}")
    print(f"  reference disagreements: {len(disagreements)}")
    print(f"  partial reference coverage: {len(partial)}")
    print(f"  simple state-equal review candidates: {len(simple)}")
    print(f"  manual/compound review candidates: {len(manual)}")
    if class_counts:
        print("  residual classes: " + ", ".join(f"{k}={v}" for k, v in sorted(class_counts.items())))
    if consensus_class_counts:
        print(
            "  consensus classes: "
            + ", ".join(f"{k}={v}" for k, v in sorted(consensus_class_counts.items()))
        )

    def print_rows(title: str, rows: list[dict]) -> None:
        if not rows:
            return
        print()
        print(title)
        print("class\tmain\tsub\torder\tcurrent\treference\tcurrentComb\treferenceComb")
        for row in sorted(
            rows,
            key=lambda item: (
                int(item.get("main_id") or 0),
                int(item.get("order") or 0),
                int(item.get("sub_id") or 0),
            ),
        ):
            print(
                "\t".join(
                    [
                        str(row.get("classification") or ""),
                        str(row.get("main_id") or 0),
                        str(row.get("sub_id") or 0),
                        str(row.get("order") or 0),
                        json.dumps(row.get("current_accept"), ensure_ascii=False, separators=(",", ":")),
                        json.dumps(row.get("reference_accept"), ensure_ascii=False, separators=(",", ":")),
                        str(row.get("current_comb") or ""),
                        str(row.get("reference_comb") or ""),
                    ]
                )
            )

    print_rows("Simple state-equal candidates (still review before repair)", simple)
    print_rows("Manual / compound consensus candidates", manual)
    print_rows("Reference disagreements (do not repair from historical consensus)", disagreements)
    print_rows("Partial coverage (do not treat as two-version consensus)", partial)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(
                {
                    "prologue_main_ids": sorted(PROLOGUE_MAIN_IDS),
                    "required_consensus_count": args.consensus_count,
                    "manifest_sub_ids": sorted(manifest_sub_ids),
                    "manifest_rows_present": len(manifest_rows),
                    "residual_counts": dict(class_counts),
                    "consensus_counts": dict(consensus_class_counts),
                    "simple": simple,
                    "manual": manual,
                    "reference_disagreements": disagreements,
                    "partial_reference_coverage": partial,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print()
        print(f"Wrote filtered JSON report: {args.json_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
