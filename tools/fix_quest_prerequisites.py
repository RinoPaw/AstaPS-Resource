#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PATH = Path("ExcelBinOutput/QuestExcelConfigData.json")
STATE_EQUAL = "QUEST_COND_STATE_EQUAL"
STATE_NOT_EQUAL = "QUEST_COND_STATE_NOT_EQUAL"
FINISHED = 3


def state_equal(quest_id: int, state: int = FINISHED) -> dict:
    return {
        "type": STATE_EQUAL,
        "param": [quest_id, state, 0],
        "param_str": "",
    }


def state_not_equal(quest_id: int, state: int = FINISHED) -> dict:
    return {
        "type": STATE_NOT_EQUAL,
        "param": [quest_id, state, 0],
        "param_str": "",
    }


@dataclass(frozen=True)
class Repair:
    json_file: str
    main_id: int
    sub_id: int
    desc_hash: int
    expected_accept: tuple[dict, ...]
    damaged_accept: tuple[tuple[dict, ...], ...]
    expected_comb: str | None = None


def one(predecessor: int, *, state: int = FINISHED) -> tuple[dict, ...]:
    return (state_equal(predecessor, state),)


# Concrete 7.1 conversion defects recovered from intact historical BinOutput. These rows deliberately
# cover more than zeroed predecessors: the converter also sequentialized parallel nodes and dropped
# additional conditions from compound accepts. Every repair names the exact damaged shape observed
# in the 7.1 dump; an unexpected meaningful condition aborts instead of being overwritten.
REPAIRS = (
    Repair("351.json", 351, 35101, 3236261087, one(35100), (one(35107),)),
    Repair("352.json", 352, 35200, 2150333847, one(35102), (one(0),)),

    # Prologue Act I: early Mondstadt graph.
    Repair("354.json", 354, 35401, 2564565335, one(35505), (one(0),)),
    Repair("354.json", 354, 35403, 1527152647, one(35404), (one(35405),)),
    Repair("355.json", 355, 35501, 1480972647, one(35311), (one(0),)),
    Repair(
        "355.json",
        355,
        35502,
        3003852887,
        (state_equal(35501), state_equal(36101), state_equal(36101)),
        ((state_equal(35501),),),
        expected_comb="LOGIC_AND",
    ),
    Repair("356.json", 356, 35601, 1893185559, one(36005), (one(0),)),
    Repair("356.json", 356, 35603, 645974095, one(35601), (one(35602),)),
    Repair("357.json", 357, 35721, 401722439, one(35606), (one(0),)),
    Repair("358.json", 358, 35800, 2056537383, one(35724), (one(0),)),

    # Temple branches fan out from 35802; the converted dump lost each cross-main predecessor.
    Repair("306.json", 306, 30600, 447310999, one(35802), (one(0),)),
    Repair("307.json", 307, 30700, 4264103487, one(35802), (one(0),)),
    Repair("308.json", 308, 30800, 4078363583, one(35802), (one(0),)),
    Repair("309.json", 309, 30901, 2918457247, one(35802), (one(0),)),
    Repair("311.json", 311, 31101, 486980247, one(30904), (one(0),)),

    # Hidden Act-I controllers. 35902/03/04 are parallel branches from 35802 in intact data.
    Repair("359.json", 359, 35901, 1736464775, one(35725), (one(0),)),
    Repair("359.json", 359, 35902, 206764287, one(35802), (one(35901),)),
    Repair("359.json", 359, 35903, 4126557215, one(35802), (one(35902),)),
    Repair("359.json", 359, 35904, 969515055, one(35802), (one(35903),)),
    Repair("360.json", 360, 36001, 4087620839, one(35403), (one(0),)),
    Repair("360.json", 360, 36003, 2320130263, one(36001), (one(0),)),
    Repair("361.json", 361, 36100, 0, one(35311), (one(0),)),
    Repair(
        "362.json",
        362,
        36203,
        0,
        (state_equal(99902), state_not_equal(35200), state_not_equal(35200)),
        ((state_equal(0),),),
        expected_comb="LOGIC_AND",
    ),

    # Chapter 1001 controller: starts the "The Outlander Who Caught the Wind" banner.
    Repair("363.json", 363, 36301, 0, one(35202), (one(0),)),

    # Prologue Act II handoff and chapter path.
    Repair("370.json", 370, 37001, 984138423, one(31101), (one(0),)),
    # Hidden trigger 37003 is active while 37005 is UNFINISHED (state 2).
    Repair("370.json", 370, 37003, 411942639, one(37005, state=2), (one(37005),)),
    Repair("371.json", 371, 37101, 3416483463, one(37005), (one(0),)),

    # Prologue Act III opening handoff.
    Repair("397.json", 397, 39701, 619581215, one(38406), (one(0),)),
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


def meaningful_entries(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict) and entry.get("type")]


def normalize_condition(entry: dict) -> dict:
    params = entry.get("param", [])
    if not isinstance(params, list):
        params = []
    if entry.get("type") in (STATE_EQUAL, STATE_NOT_EQUAL) and len(params) >= 2:
        # Historical fixed-width data retains an unused trailing zero; the flattened 7.1 dump often
        # omits it. AstaPS's state comparison reads only quest id and state.
        params = params[:2]
    return {
        "type": entry.get("type"),
        "param": params,
        "param_str": entry.get("param_str", entry.get("paramStr", "")) or "",
    }


def normalize_accept(value) -> list[dict]:
    return [normalize_condition(entry) for entry in meaningful_entries(value)]


def normalized_variant(value: tuple[dict, ...]) -> list[dict]:
    return normalize_accept(list(value))


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


def render_object(obj: dict) -> str:
    """Render one list element with the repository's two-space outer indentation."""
    raw = json.dumps(obj, ensure_ascii=False, indent=2)
    lines = raw.splitlines()
    return lines[0] + "\n" + "\n".join("  " + line for line in lines[1:])


def patch_object(raw: str, repair: Repair) -> tuple[str, str, list[str]]:
    obj = json.loads(raw)
    current = normalize_accept(obj.get("acceptCond"))
    expected = normalized_variant(repair.expected_accept)
    damaged = [normalized_variant(variant) for variant in repair.damaged_accept]
    changes: list[str] = []

    if current == expected:
        pass
    elif current in damaged:
        obj["acceptCond"] = [dict(entry) for entry in repair.expected_accept]
        changes.append(f"acceptCond={expected!r}")
    else:
        raise ValueError(
            f"Quest {repair.sub_id} has unexpected meaningful acceptCond: {current!r}; "
            f"expected {expected!r} or one of damaged variants {damaged!r}"
        )

    if repair.expected_comb is not None:
        current_comb = obj.get("acceptCondComb")
        if current_comb == repair.expected_comb:
            pass
        elif current_comb in (None, "", "LOGIC_NONE"):
            obj["acceptCondComb"] = repair.expected_comb
            changes.append(f"acceptCondComb={repair.expected_comb}")
        else:
            raise ValueError(
                f"Quest {repair.sub_id} has unexpected acceptCondComb={current_comb!r}; "
                f"expected missing or {repair.expected_comb}"
            )

    if not changes:
        return raw, "already-correct", []

    # Reformat only this quest row, not the multi-million-line generated resource.
    patched = render_object(obj)
    parsed = json.loads(patched)
    if normalize_accept(parsed.get("acceptCond")) != expected:
        raise ValueError(f"Quest {repair.sub_id} repair did not survive JSON validation")
    if repair.expected_comb is not None and parsed.get("acceptCondComb") != repair.expected_comb:
        raise ValueError(f"Quest {repair.sub_id} logic repair did not survive JSON validation")
    return patched, "changed", changes


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

    found: dict[int, tuple[str, list[str]]] = {}
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

        patched, status, changes = patch_object(raw, repair)
        found[repair.sub_id] = (status, changes)
        if status == "changed":
            replacements.append((start, end, patched))

    missing = [repair.sub_id for repair in REPAIRS if repair.sub_id not in found]
    if missing:
        raise SystemExit(f"Expected quest rows not found: {missing}")

    for repair in REPAIRS:
        status, changes = found[repair.sub_id]
        detail = ", ".join(changes) if changes else "verified"
        print(f"Quest {repair.sub_id}: {status}: {detail}")

    if args.check:
        if replacements:
            print(f"Pending repaired quest rows: {len(replacements)}")
            return 1
        print("All evidence-backed quest prerequisite repairs are already applied.")
        return 0

    if not replacements:
        print("Nothing to do; the resource is already fixed.")
        return 0

    patched_text = text
    for start, end, patched in reversed(replacements):
        patched_text = patched_text[:start] + patched + patched_text[end:]

    parsed = json.loads(patched_text)
    if not isinstance(parsed, list):
        raise SystemExit("Patched resource unexpectedly stopped being a JSON array")

    target_ids = {repair.sub_id for repair in REPAIRS}
    by_sub_id = {
        int(obj.get("subId") or 0): obj
        for obj in parsed
        if isinstance(obj, dict) and int(obj.get("subId") or 0) in target_ids
    }
    for repair in REPAIRS:
        probe = by_sub_id.get(repair.sub_id)
        if probe is None:
            raise SystemExit(f"Quest {repair.sub_id} disappeared after patch")
        if normalize_accept(probe.get("acceptCond")) != normalized_variant(repair.expected_accept):
            raise SystemExit(f"Quest {repair.sub_id} failed post-write acceptCond validation")
        if repair.expected_comb is not None and probe.get("acceptCondComb") != repair.expected_comb:
            raise SystemExit(f"Quest {repair.sub_id} failed post-write logic validation")

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(patched_text, encoding="utf-8", newline="")
    os.replace(tmp, path)

    print(f"Updated: {path}")
    print(f"Repaired quest rows: {len(replacements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
