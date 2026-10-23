#!/usr/bin/env python3
"""Audit 7.1 BlossomGroups -> Lua coverage. No coordinates are inferred.

Source availability does not authenticate a Lua file or a camp table against the
original Global 7.1 executable, metadata or original asset bundles.
"""
import argparse
import json
import re
from pathlib import Path

GADGET_IDS = {70360056: "gold", 70360057: "blue"}
GADGET_PATTERN = re.compile(r"\bgadget_id\s*=\s*(\d+)")
LUA_LINE_COMMENT = re.compile(r"--[^\n]*")


def inspect_script(path: Path) -> dict:
    if not path.is_file():
        return {"status": "missing", "kinds": [], "generated": False}
    text = path.read_text(encoding="utf-8-sig")
    uncommented = LUA_LINE_COMMENT.sub("", text)
    kinds = sorted({GADGET_IDS[int(id_)] for id_ in GADGET_PATTERN.findall(uncommented)
                    if int(id_) in GADGET_IDS})
    return {"status": "present", "kinds": kinds,
            "generated": text.lstrip().startswith("-- Auto-generated spawn data")}


def audit(root: Path, city_id: int, rank: int, scene_id: int) -> dict:
    camps = json.loads((root / "ExcelBinOutput" /
                        "BlossomGroupsExcelConfigData.json").read_text(encoding="utf-8-sig"))
    eligible = sorted((row for row in camps
                       if row.get("cityId") == city_id
                       and row.get("limit_level", 0) <= rank
                       and any(t in (1, 3) for t in row.get("refreshTypeVec", []))
                       and row.get("newGroupVec")), key=lambda row: row["id"])
    rows = []
    for camp in eligible:
        groups = []
        for group_id in camp["newGroupVec"]:
            script = (root / "Scripts" / "Scene" / str(scene_id)
                      / f"scene{scene_id}_group{group_id}.lua")
            groups.append({"groupId": group_id,
                           "script": script.relative_to(root).as_posix(),
                           **inspect_script(script)})
        rows.append({"campId": camp["id"], "sectionId": camp.get("sectionId"),
                     "groups": groups})
    members = [group for row in rows for group in row["groups"]]
    return {
        "cityId": city_id, "sceneId": scene_id, "adventureRank": rank,
        "originalClientVerified": False,
        "summary": {
            "eligibleCamps": len(rows),
            "referencedGroups": len(members),
            "missingGroups": sum(g["status"] == "missing" for g in members),
            "presentGroups": sum(g["status"] == "present" for g in members),
            "generatedGroups": sum(g["generated"] for g in members),
            "blueGroups": sum("blue" in g["kinds"] for g in members),
            "goldGroups": sum("gold" in g["kinds"] for g in members),
        },
        "camps": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--city", type=int, default=5)
    parser.add_argument("--scene", type=int, default=3)
    parser.add_argument("--rank", type=int, default=18)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.root, args.city, args.rank, args.scene)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    s = report["summary"]
    print(f"City {args.city}, scene {args.scene}, AR {args.rank}: "
          f"{s['eligibleCamps']} camps, {s['presentGroups']}/{s['referencedGroups']} "
          f"Lua groups present; blue={s['blueGroups']}, gold={s['goldGroups']}, "
          f"auto-generated={s['generatedGroups']}.")
    print("No Lua or coordinate source has been authenticated against original 7.1.")
    for camp in report["camps"]:
        for group in camp["groups"]:
            state = ("missing" if group["status"] == "missing"
                     else "/".join(group["kinds"]) or "no ley-line gadget")
            suffix = " (auto-generated)" if group["generated"] else ""
            print(f"  camp={camp['campId']} group={group['groupId']}: {state}{suffix}")


if __name__ == "__main__":
    main()
