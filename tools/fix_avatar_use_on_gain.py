#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


DEFAULT_PATH = Path("ExcelBinOutput/MaterialExcelConfigData.json")
TARGET_MATERIAL_TYPE = "MATERIAL_AVATAR"
TARGET_USE_OP = "ITEM_USE_GAIN_AVATAR"


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


def is_avatar_gain_record(obj: dict) -> bool:
    if obj.get("materialType") != TARGET_MATERIAL_TYPE:
        return False

    item_use = obj.get("itemUse")
    if not isinstance(item_use, list):
        return False

    return any(
        isinstance(action, dict) and action.get("useOp") == TARGET_USE_OP
        for action in item_use
    )


def patch_object(raw: str) -> tuple[str, bool]:
    obj = json.loads(raw)

    if not isinstance(obj, dict) or not is_avatar_gain_record(obj):
        return raw, False

    if obj.get("useOnGain") is True:
        return raw, False

    if "useOnGain" in obj:
        patched, count = re.subn(
            r'(?m)^([ \t]*"useOnGain"[ \t]*:[ \t]*)(?:false|null)([ \t]*,?[ \t]*)$',
            r"\1true\2",
            raw,
            count=1,
        )
        if count != 1:
            raise ValueError(
                f'Avatar item {obj.get("id")} has an unexpected useOnGain representation'
            )
        return patched, True

    newline = "\r\n" if "\r\n" in raw else "\n"

    field_match = re.search(r'(?m)^([ \t]+)"[^"]+"[ \t]*:', raw)
    if not field_match:
        raise ValueError(f'Could not determine indentation for avatar item {obj.get("id")}')
    field_indent = field_match.group(1)

    close_match = re.search(r'(\r?\n)([ \t]*)\}$', raw)
    if not close_match:
        raise ValueError(f'Could not locate closing brace for avatar item {obj.get("id")}')

    insert_at = close_match.start()
    patched = (
        raw[:insert_at]
        + ","
        + newline
        + field_indent
        + '"useOnGain": true'
        + raw[insert_at:]
    )
    return patched, True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fix AstaPS 7.1 avatar material records so ITEM_USE_GAIN_AVATAR "
            "runs immediately when the item is obtained."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_PATH,
        help=f"MaterialExcelConfigData.json path (default: {DEFAULT_PATH})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report what would change without writing the file.",
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

    replacements: list[tuple[int, int, str]] = []
    matched_ids: list[int | str] = []
    changed_ids: list[int | str] = []
    already_true = 0

    for start, end in iter_top_level_objects(text):
        raw = text[start:end]
        obj = json.loads(raw)
        if not isinstance(obj, dict) or not is_avatar_gain_record(obj):
            continue

        item_id = obj.get("id", "?")
        matched_ids.append(item_id)

        if obj.get("useOnGain") is True:
            already_true += 1
            continue

        patched, changed = patch_object(raw)
        if changed:
            replacements.append((start, end, patched))
            changed_ids.append(item_id)

    if not matched_ids:
        raise SystemExit(
            "No MATERIAL_AVATAR + ITEM_USE_GAIN_AVATAR records were found. "
            "Check that you pointed the script at the expected AstaPS resource file."
        )

    print(f"Matched avatar gain records : {len(matched_ids)}")
    print(f"Already useOnGain=true     : {already_true}")
    print(f"Need modification          : {len(changed_ids)}")

    if changed_ids:
        preview = ", ".join(map(str, changed_ids[:20]))
        if len(changed_ids) > 20:
            preview += f", ... (+{len(changed_ids) - 20} more)"
        print(f"Changed item ids           : {preview}")

    if args.check:
        print("Check only; file was not modified.")
        return 0

    if not replacements:
        print("Nothing to do; the resource is already fixed.")
        return 0

    patched_text = text
    for start, end, patched in reversed(replacements):
        patched_text = patched_text[:start] + patched + patched_text[end:]

    json.loads(patched_text)

    patched_bytes = patched_text.encode("utf-8")
    if patched_bytes == original_bytes:
        print("Nothing changed.")
        return 0

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(patched_bytes)
    os.replace(tmp, path)

    print(f"Updated: {path}")
    print("Run git diff on the file before starting AstaPS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
