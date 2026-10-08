#!/usr/bin/env python3
"""Report historical-compatibility Quest prerequisites versus flattened Excel.

This is evidence discovery: it does not claim native 7.1 acceptCond ownership
and does not rewrite either dataset.
"""
import json
from collections import Counter
from pathlib import Path
from audit_mondstadt_prologue import SCOPE


def normalize(conds):
    return [
        {"type": c.get("type"), "param": c.get("param", []),
         "param_str": c.get("param_str", c.get("_param_str", ""))}
        for c in (conds or []) if c.get("type")
    ]


def main():
    excel = {
        row["subId"]: row
        for row in json.loads(Path("ExcelBinOutput/QuestExcelConfigData.json").read_text(encoding="utf-8"))
        if isinstance(row, dict) and isinstance(row.get("subId"), int)
    }
    results, counts = [], Counter()
    for stage, ids in SCOPE.items():
        for main_id in ids:
            quest = json.loads(Path("BinOutput/Quest/%d.json" % main_id).read_text(encoding="utf-8"))
            for row in quest["subQuests"]:
                sub = row["subId"]
                current = excel.get(sub)
                if current is None:
                    results.append({"stage": stage, "sub": sub, "difference": "missing_excel"})
                    counts[(stage, "missing_excel")] += 1
                    continue
                a = normalize(row.get("acceptCond"))
                b = normalize(current.get("acceptCond"))
                left_comb = row.get("acceptCondComb", "LOGIC_NONE")
                right_comb = current.get("acceptCondComb", "LOGIC_NONE")
                if a != b or left_comb != right_comb:
                    item = {"stage": stage, "main": main_id, "sub": sub,
                            "binCompatConditions": a, "excelConditions": b,
                            "binComb": left_comb, "excelComb": right_comb}
                    results.append(item)
                    counts[(stage, "accept_drift")] += 1
                for field in ("beginExec", "finishExec", "failExec"):
                    be = [x for x in row.get(field, []) if x.get("type")]
                    ex = [x for x in current.get(field, []) if x.get("type")]
                    if ex and be and be != ex:
                        counts[(stage, "action_conflict")] += 1
                        results.append({"stage": stage, "main": main_id, "sub": sub,
                                        "field": field, "binActions": be, "excelActions": ex})
    payload = {
        "scope": "Genshin 7.1 Mondstadt prelude / Acts I-III",
        "sourceLabels": {
            "bin": "historical compatibility, not 7.1 native acceptCond",
            "excel": "flattened Asta materialization (may be synthetic)",
        },
        "counts": {"%s:%s" % k: v for k, v in sorted(counts.items())},
        "differences": results,
    }
    path = Path("mondstadt-quest-drift.json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SCOPED DRIFT counts:", json.dumps(payload["counts"], sort_keys=True))
    print("SCOPED DRIFT sample:", json.dumps(results[:12], ensure_ascii=False)[:12000])
    print("REPORT", path, "differences", len(results))


if __name__ == "__main__":
    main()
