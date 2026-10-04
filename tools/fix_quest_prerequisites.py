#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PATH = Path("ExcelBinOutput/QuestExcelConfigData.json")
STATE_EQUAL = "QUEST_COND_STATE_EQUAL"
FINISHED = 3


@dataclass(frozen=True)
class Repair:
    json_file: str
    main_id: int
    sub_id: int
    desc_hash: int
    broken_predecessor: int
    correct_predecessor: int


# These are concrete 7.1 conversion defects recovered from intact historical BinOutput.
# Keep this list evidence-backed and deliberately non-generic.
REPAIRS = (
    # Early Mondstadt onboarding / Prologue Act I.
    Repair(
        json_file="351.json",
        main_id=351,
        sub_id=35101,
        desc_hash=3236261087,
        broken_predecessor=35107,
        correct_predecessor=35100,
    ),
    Repair(
        json_file="352.json",
        main_id=352,
        sub_id=35200,
        desc_hash=2150333847,
        broken_predecessor=0,
        correct_predecessor=35102,
    ),
    Repair(
        json_file="363.json",
        main_id=363,
        sub_id=36301,
        desc_hash=0,
        broken_predecessor=0,
        correct_predecessor=35202,
    ),
    Repair(
        json_file="355.json",
        main_id=355,
        sub_id=35501,
        desc_hash=1480972647,
        broken_predecessor=0,
        correct_predecessor=35311,
    ),
    Repair(
        json_file="354.json",
        main_id=354,
        sub_id=35401,
        desc_hash=2564565335,
        broken_predecessor=0,
        correct_predecessor=35505,
    ),
    Repair(
        json_file="360.json",
        main_id=360,
        sub_id=36001,
        desc_hash=4087620839,
        broken_predecessor=0,
        correct_predecessor=35403,
    ),
    Repair(
        json_file="356.json",
        main_id=356,
        sub_id=35601,
        desc_hash=1893185559,
        broken_predecessor=0,
        correct_predecessor=36005,
    ),
    Repair(
        json_file="357.json",
        main_id=357,
        sub_id=35721,
        desc_hash=401722439,
        broken_predecessor=0,
        correct_predecessor=35606,
    ),
    Repair(
        json_file="358.json",
        main_id=358,
        sub_id=35800,
        desc_hash=2056537383,
        broken_predecessor=0,
        correct_predecessor=35724,
    ),
    # The three temple branches and the hidden completion controller all fan out from 35802.
    Repair(
        json_file="306.json",
        main_id=306,
        sub_id=30600,
        desc_hash=447310999,
        broken_predecessor=0,
        correct_predecessor=35802,
    ),
    Repair(
        json_file="307.json",
        main_id=307,
        sub_id=30700,
        desc_hash=4264103487,
        broken_predecessor=0,
        correct_predecessor=35802,
    ),
    Repair(
        json_file="308.json",
        main_id=308,
        sub_id=30800,
        desc_hash=4078363583,
        broken_predecessor=0,
        correct_predecessor=35802,
    ),
    Repair(
        json_file="309.json",
        main_id=309,
        sub_id=30901,
        desc_hash=2918457247,
        broken_predecessor=0,
        correct_predecessor=35802,
    ),
    Repair(
        json_file="311.json",
        main_id=311,
        sub_id=31101,
        desc_hash=486980247,
        broken_predecessor=0,
        correct_predecessor=30904,
    ),
    # Prologue Act II and III entry handoffs.
    Repair(
        json_file="370.json",
        main_id=370,
        sub_id=37001,
        desc_hash=984138423,
        broken_predecessor=0,
        correct_predecessor=31101,
    ),
    Repair(
        json_file="397.json",
        main_id=397,
        sub_id=39701,
        desc_hash=619581215,
        broken_predecessor=0,
        correct_predecessor=38406,
    ),
)


def iter_top_level_objects(text: str):
    """Yield (start, end) slices for objects in the top-level JSON array."""
    depth = 0
    in_string = False
    escaped = False
    start = None

    for i, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth == 0:
                raise ValueError(f"Unexpected closing brace at offset {i}")
            depth -= 1
            if depth == 0 and start is not None:
                yield start, i + 1
                start = None

    if in_string:
        raise ValueError("Unterminated JSON string")
    if depth != 0:
        raise ValueError("Unbalanced JSON object braces")


def identify_repair(obj: dict) -> Repair | None:
    for repair in REPAIRS:
        if (
            obj.get("json_file") == repair.json_file
            and obj.get("mainId") == repair.main_id
            and obj.get("subId") == repair.sub_id
            and obj.get("descTextMapHash") == repair.desc_hash
        ):
            return repair
    return None


def prerequisite(obj: dict) -> tuple[str | None, list[int] | None]:
    conditions = obj.get("acceptCond")
    if not isinstance(conditions, list) or len(conditions) != 1:
        return None, None

    condition = conditions[0]
    if not isinstance(condition, dict):
        return None, None

    params = condition.get("param")
    if not isinstance(params, list):
        return condition.get("type"), None

    return condition.get("type"), params


def patch_object(raw: str, repair: Repair) -> tuple[str, str]:
    obj = json.loads(raw)
    cond_type, params = prerequisite(obj)

    if cond_type != STATE_EQUAL or params is None or len(params) < 2 or params[1] != FINISHED:
        raise ValueError(
            f"Quest {repair.sub_id} has an unexpected accept condition: "
            f"type={cond_type!r}, params={params!r}"
        )

    predecessor = params[0]
    if predecessor == repair.correct_predecessor:
        return raw, "already-correct"
    if predecessor != repair.broken_predecessor:
        raise ValueError(
            f"Quest {repair.sub_id} predecessor is {predecessor}; expected broken "
            f"{repair.broken_predecessor} or corrected {repair.correct_predecessor}"
        )

    # Replace only the first integer in the sole acceptCond param array. Keeping the original
    # object text intact avoids reformatting a ~40 MiB generated resource file.
    pattern = re.compile(
        r'("acceptCond"\s*:\s*\[\s*\{.*?"type"\s*:\s*"QUEST_COND_STATE_EQUAL"'
        r'.*?"param"\s*:\s*\[\s*)'
        + re.escape(str(repair.broken_predecessor))
        + r'(\s*,\s*3\b)',
        re.DOTALL,
    )
    patched, count = pattern.subn(
        lambda m: m.group(1) + str(repair.correct_predecessor) + m.group(2),
        raw,
        count=1,
    )
    if count != 1:
        raise ValueError(f"Could not patch quest {repair.sub_id} without reformatting its record")

    parsed = json.loads(patched)
    _, patched_params = prerequisite(parsed)
    if patched_params is None or patched_params[0] != repair.correct_predecessor:
        raise ValueError(f"Quest {repair.sub_id} repair did not survive JSON validation")

    return patched, "changed"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repair evidence-backed 7.1 quest prerequisite conversion defects."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_PATH,
        help=f"QuestExcelConfigData.json path (default: {DEFAULT_PATH})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the known rows and report pending repairs without writing the file.",
    )
    args = parser.parse_args()

    path: Path = args.path
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    original_bytes = path.read_bytes()
    try:
        text = original_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"{path} is not UTF-8: {exc}") from exc

    root = json.loads(text)
    if not isinstance(root, list):
        raise SystemExit(f"{path} must contain a top-level JSON array")

    found: dict[int, str] = {}
    replacements: list[tuple[int, int, str]] = []

    for start, end in iter_top_level_objects(text):
        raw = text[start:end]
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            continue

        repair = identify_repair(obj)
        if repair is None:
            continue
        if repair.sub_id in found:
            raise SystemExit(f"Quest {repair.sub_id} appears more than once in {path}")

        patched, status = patch_object(raw, repair)
        found[repair.sub_id] = status
        if status == "changed":
            replacements.append((start, end, patched))

    missing = [repair.sub_id for repair in REPAIRS if repair.sub_id not in found]
    if missing:
        raise SystemExit(f"Expected quest rows not found: {missing}")

    for repair in REPAIRS:
        status = found[repair.sub_id]
        print(
            f"Quest {repair.sub_id}: {repair.broken_predecessor} -> "
            f"{repair.correct_predecessor}: {status}"
        )

    if args.check:
        if replacements:
            print(f"Pending repairs: {len(replacements)}")
            return 1
        print("All known quest prerequisite repairs are already applied.")
        return 0

    if not replacements:
        print("Nothing to do; the resource is already fixed.")
        return 0

    patched_text = text
    for start, end, patched in reversed(replacements):
        patched_text = patched_text[:start] + patched + patched_text[end:]

    # Validate the complete generated resource before replacing it atomically.
    json.loads(patched_text)
    patched_bytes = patched_text.encode("utf-8")

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(patched_bytes)
    os.replace(tmp, path)

    print(f"Updated: {path}")
    print(f"Applied repairs: {len(replacements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
