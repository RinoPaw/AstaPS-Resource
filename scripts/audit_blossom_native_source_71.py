#!/usr/bin/env python3
"""Audit imported 7.1 Blossom camp groups and probe the flat scene index.

This is a *resource coverage* tool. Neither a Lua file nor a matching string
in the flat index authenticates coordinates against the Global 7.1 EXE.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMP_JSON = ROOT / "ExcelBinOutput/BlossomGroupsExcelConfigData.json"
FLAT = ROOT / "ScriptSceneData/flat.luas.scenes.full_globals.lua.json"
CITIES = range(1, 9)
BLOSSOM_TYPES = {1, 3}
FONT = 5
LOOK_FOR = (133403311, 133403313, 133412176, 133412177, 133412178, 70360056, 70360057)


def scene3_files() -> set[str]:
    paths = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "HEAD:Scripts/Scene/3"],
        text=True,
    )
    return set(paths.splitlines())


def eligible(rows: list[dict], city: int) -> list[dict]:
    return [row for row in rows
            if row.get("cityId") == city
            and BLOSSOM_TYPES.intersection(row.get("refreshTypeVec") or [])
            and row.get("newGroupVec")]


def audit() -> None:
    rows = json.loads(CAMP_JSON.read_text(encoding="utf-8"))
    paths = scene3_files()
    print(f"Resource graph: {len(rows)} BlossomGroups rows; scene 3 has {len(paths)} tree entries")
    for city in CITIES:
        camps = eligible(rows, city)
        ids = sorted({gid for row in camps for gid in row["newGroupVec"]})
        found = [gid for gid in ids if f"scene3_group{gid}.lua" in paths]
        print(f"city={city} camps={len(camps)} groups={len(ids)} "
              f"lua_present={len(found)} lua_missing={len(ids)-len(found)}")
        if city != FONT:
            continue
        for row in camps:
            for gid in row["newGroupVec"]:
                filename = f"scene3_group{gid}.lua"
                present = filename in paths
                suffix = ""
                if present:
                    contents = (ROOT / "Scripts/Scene/3" / filename).read_text(encoding="utf-8")
                    gadgets = sorted(set(re.findall(r"\\bgadget_id\\s*=\\s*(\\d+)", contents)))
                    suffix = f" gadget_ids={gadgets} auto_generated={'Auto-generated' in contents}"
                print(f" fontaine camp={row['id']} group={gid} lua={present}{suffix}")

    if not FLAT.exists():
        print("Flat index unavailable")
        return
    contents = FLAT.read_text(encoding="utf-8")
    print(f"Flat scene index: file_bytes={FLAT.stat().st_size}, "
          f"text_chars={len(contents)} prefix={contents[:100]!r}")
    for value in LOOK_FOR:
        matches = list(re.finditer(r"(?<!\\d)" + str(value) + r"(?!\\d)", contents))
        print(f" flat_index exact_number={value} occurrences={len(matches)}")
        for m in matches[:2]:
            nearby = contents[max(0, m.start() - 130):m.end() + 160]
            print(f"  offset={m.start()} context={nearby!r}")
    try:
        root = json.loads(contents)
        if isinstance(root, dict):
            print(f"Flat index root: dict len={len(root)} first_keys={list(root)[:15]}")
        elif isinstance(root, list):
            print(f"Flat index root: list len={len(root)}")
        else:
            print(f"Flat index root: {type(root).__name__}")
    except (ValueError, MemoryError) as err:
        print(f"Flat index JSON structure unavailable: {type(err).__name__}: {err}")


if __name__ == "__main__":
    audit()
