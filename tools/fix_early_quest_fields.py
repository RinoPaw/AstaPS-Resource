#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path


DEFAULT_PATH = Path("ExcelBinOutput/QuestExcelConfigData.json")


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


def meaningful_entries(value):
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict) and entry.get("type")]


def exec_entry(exec_type: str, params: list[str]) -> dict:
    return {"param": params, "type": exec_type}


def state_equal(quest_id: int) -> dict:
    return {
        "param": [quest_id, 3, 0],
        "param_str": "",
        "type": "QUEST_COND_STATE_EQUAL",
    }


# Evidence source: intact pre-obfuscation Quest data for the same Mondstadt chain.
# Recovery is monotonic: all upstream acceptCond and beginExec entries are retained, and only
# evidence-backed missing entries are appended.
EXPECTED_BEGIN_EXECS = {
    35104: [exec_entry("QUEST_EXEC_SET_IS_GAME_TIME_LOCKED", ["1"])],
    35301: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003002,1"])],
    35302: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003002,2"])],
    35303: [exec_entry("QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003448"])],
    35304: [
        exec_entry("QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003449"]),
        exec_entry("QUEST_EXEC_ADD_CUR_AVATAR_ENERGY", []),
    ],
    # Forest Rendezvous hidden plot controller. This suite is active only while 36100 is running.
    36100: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003436,1"])],
    30904: [exec_entry("QUEST_EXEC_ADD_QUEST_PROGRESS", ["359011", "1"])],
    35404: [exec_entry("QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003439"])],
    35901: [exec_entry("QUEST_EXEC_SET_WEATHER_GADGET", ["3", "1"])],
    36001: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003435,1"])],
    36003: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003136,1"])],
    37303: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133001305,2"])],
    38202: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133001249,2"])],
    38905: [exec_entry("QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133007227"])],
    39003: [exec_entry("QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133007227"])],
    39401: [exec_entry("QUEST_EXEC_UNLOCK_POINT", ["3", "38"])],
    39604: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133001910,2"])],
    39703: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133002233,2"])],
    39801: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003910,2"])],
    39808: [exec_entry("QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133004917,1"])],
    39812: [exec_entry("QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003910"])],
}

EXPECTED_ACCEPT = {
    35301: [state_equal(35205)],
    35312: [state_equal(35205)],
    35302: [state_equal(35301)],
    35309: [state_equal(35302)],
    35303: [state_equal(35309)],
    35310: [state_equal(35303)],
    35304: [state_equal(35310)],
    35311: [state_equal(35304)],
    # Forest Rendezvous (main 355) starts after Unexpected Power is fully complete.
    35501: [state_equal(35311)],
    35502: [state_equal(35501), state_equal(36101), state_equal(36101)],
    35503: [state_equal(35502)],
    35504: [state_equal(35503)],
    35505: [state_equal(35504)],
    # Hidden Dvalin plot controller paired with visible quest 35501.
    36100: [state_equal(35311)],
    36101: [state_equal(36100)],
}

# Exact converter-damaged variants observed in the 7.1 dump. Keep these per-subquest instead of
# accepting arbitrary alternative predecessors: 35312 was serialized as a sequential successor of
# 35301 even though the intact graph starts both from 35205; some dumps then serialize 35302 after
# 35312 for the same reason. Forest Rendezvous 35502 can retain only the visible 35501 predecessor
# while dropping both hidden 36101 prerequisites.
KNOWN_DAMAGED_ACCEPT = {
    35312: [[state_equal(35301)]],
    35302: [[state_equal(35312)]],
    35502: [[state_equal(35501)]],
}

EXPECTED_LOGIC = {
    35100: {"finishCondComb": "LOGIC_OR"},
    35103: {"acceptCondComb": "LOGIC_AND"},
    35102: {"acceptCondComb": "LOGIC_OR"},
    35201: {"finishCondComb": "LOGIC_OR"},
    # The overlook step must wait for BOTH FINISH_PLOT(35203) and trigger 1172
    # (Scene 3 / group 133003901 / ENTER_REGION_901002).
    35203: {"finishCondComb": "LOGIC_AND", "failCondComb": "LOGIC_OR"},
    # The next visible Forest Rendezvous step waits for the visible approach task and the hidden
    # Dvalin plot controller to both finish.
    35502: {"acceptCondComb": "LOGIC_AND"},
    # Hidden controller 30901 completes only after all three early temple dungeons are finished.
    30901: {"finishCondComb": "LOGIC_AND"},
    # 31101 accepts either of the two Paimon talks depending on the hidden 46904 branch state.
    31101: {"finishCondComb": "LOGIC_OR"},
    # 35901 may complete through either the plot completion or the explicit quest-progress signal.
    35901: {"finishCondComb": "LOGIC_OR"},
}

TARGETS = set(EXPECTED_BEGIN_EXECS) | set(EXPECTED_ACCEPT) | set(EXPECTED_LOGIC)
EXPECTED_MAIN = {
    30901: 309,
    31101: 311,
    35100: 351,
    35102: 351,
    35103: 351,
    35104: 351,
    35201: 352,
    35203: 352,
    35301: 353,
    35302: 353,
    35303: 353,
    35304: 353,
    35309: 353,
    35310: 353,
    35311: 353,
    35312: 353,
    35501: 355,
    35502: 355,
    35503: 355,
    35504: 355,
    35505: 355,
    36100: 361,
    36101: 361,
    30904: 309,
    35404: 354,
    35901: 359,
    36001: 360,
    36003: 360,
    37303: 373,
    38202: 382,
    38905: 389,
    39003: 390,
    39401: 394,
    39604: 396,
    39703: 397,
    39801: 398,
    39808: 398,
    39812: 398,
}


def normalized_execs(value):
    return [
        {"type": entry.get("type"), "param": entry.get("param", [])}
        for entry in meaningful_entries(value)
    ]


def normalized_accept(value):
    out = []
    for entry in meaningful_entries(value):
        params = entry.get("param", [])
        if entry.get("type") == "QUEST_COND_STATE_EQUAL" and len(params) >= 2:
            # Converter variants differ only in whether the unused trailing zero is emitted.
            params = params[:2]
        out.append(
            {
                "type": entry.get("type"),
                "param": params,
                "param_str": entry.get("param_str", entry.get("paramStr", "")) or "",
            }
        )
    return out


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
    counts = Counter(key for entry in merged if (key := key_fn(entry)) is not None)
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


def patch_record(obj: dict) -> list[str]:
    sub_id = obj.get("subId")
    if sub_id not in TARGETS:
        return []

    expected_main = EXPECTED_MAIN[sub_id]
    if obj.get("mainId") != expected_main:
        raise ValueError(
            f"Quest {sub_id} has mainId={obj.get('mainId')}; expected {expected_main}"
        )

    changes: list[str] = []

    expected_accept = EXPECTED_ACCEPT.get(sub_id)
    if expected_accept is not None:
        merged_accept = merge_entries_preserving_existing(
            obj.get("acceptCond"), expected_accept, accept_key
        )
        if obj.get("acceptCond") != merged_accept:
            added = len(merged_accept) - len(obj.get("acceptCond") or [])
            obj["acceptCond"] = merged_accept
            changes.append(f"acceptCond+{added}")

    expected_execs = EXPECTED_BEGIN_EXECS.get(sub_id)
    if expected_execs is not None:
        merged_execs = merge_entries_preserving_existing(
            obj.get("beginExec"), expected_execs, exec_key
        )
        if obj.get("beginExec") != merged_execs:
            added = len(merged_execs) - len(obj.get("beginExec") or [])
            obj["beginExec"] = merged_execs
            changes.append(f"beginExec+{added}")

    for field, expected in EXPECTED_LOGIC.get(sub_id, {}).items():
        current = obj.get(field)
        if current == expected:
            continue
        if current not in (None, "", "LOGIC_NONE"):
            raise ValueError(
                f"Quest {sub_id} has unexpected {field}={current!r}; expected missing or {expected}"
            )
        obj[field] = expected
        changes.append(f"{field}={expected}")

    return changes


def render_object(obj: dict) -> str:
    """Render one list element with the repository's two-space outer indentation."""
    raw = json.dumps(obj, ensure_ascii=False, indent=2)
    lines = raw.splitlines()
    return lines[0] + "\n" + "\n".join("  " + line for line in lines[1:])


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recover evidence-backed early Archon quest fields lost by the 7.1 resource conversion."
        )
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
        help="Validate the target rows and report pending repairs without writing.",
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

    found: set[int] = set()
    replacements: list[tuple[int, int, str]] = []
    pending: dict[int, list[str]] = {}

    for start, end in iter_top_level_objects(text):
        raw = text[start:end]
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            continue

        sub_id = obj.get("subId")
        if sub_id not in TARGETS:
            continue
        if sub_id in found:
            raise SystemExit(f"Quest {sub_id} appears more than once in {path}")
        found.add(sub_id)

        before = json.loads(raw)
        changes = patch_record(obj)
        assert_monotonic_quest_fields(before, obj)
        if changes:
            pending[sub_id] = changes
            replacements.append((start, end, render_object(obj)))

    missing = sorted(TARGETS - found)
    if missing:
        raise SystemExit(f"Expected quest rows not found: {missing}")

    for sub_id in sorted(TARGETS):
        if sub_id in pending:
            print(f"Quest {sub_id}: pending: {', '.join(pending[sub_id])}")
        else:
            print(f"Quest {sub_id}: already correct")

    if args.check:
        if replacements:
            print(f"Pending repaired quest rows: {len(replacements)}")
            return 1
        print("All evidence-backed early quest fields are already restored.")
        return 0

    if not replacements:
        print("Nothing to do; the resource is already fixed.")
        return 0

    patched_text = text
    for start, end, patched in reversed(replacements):
        patched_text = patched_text[:start] + patched + patched_text[end:]

    # Validate the complete generated resource before replacing it atomically.
    parsed = json.loads(patched_text)
    if not isinstance(parsed, list):
        raise SystemExit("Patched resource unexpectedly stopped being a JSON array")

    by_sub_id = {
        obj.get("subId"): obj
        for obj in parsed
        if isinstance(obj, dict) and obj.get("subId") in TARGETS
    }
    for sub_id in sorted(TARGETS):
        probe = dict(by_sub_id[sub_id])
        if patch_record(probe):
            raise SystemExit(f"Quest {sub_id} did not pass post-write semantic validation")

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(patched_text, encoding="utf-8", newline="")
    os.replace(tmp, path)

    print(f"Updated: {path}")
    print(f"Repaired quest rows: {len(replacements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
