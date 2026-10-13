#!/usr/bin/env python3
"""Full 7.1 scene-script chest metadata and structural drop-root coverage audit."""
import collections
import json
import re
from pathlib import Path

ROOT = Path(".")
SCENES = ROOT / "Scripts/Scene"
DROP_ROOT = ROOT / "Server"
SERVER = ROOT / "upstream-server/data"
id_pattern = re.compile(r"\bgadget_id\s*=\s*(\d+)")
field_pattern = lambda field: re.compile(r"\b" + field + r"\s*=\s*(\d+)")
tag_pattern = re.compile(r"""\bdrop_tag\s*=\s*["']([^"']+)["']""")
table_pattern = re.compile(r"\bgadgets\s*=\s*\{")
scene_pattern = re.compile(r"scene(\d+)_group")
def read_json(path, default=None):
    if not path.exists():
        print("MISSING FILE", path)
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)
def gadget_objects(text):
    # Balanced braces allow pos/rot/explore subtables and multi-line entries.
    for m in table_pattern.finditer(text):
        depth = 0
        entry_start = None
        quote = None
        escape = False
        comment = False
        for i in range(m.end() - 1, len(text)):
            ch = text[i]
            if comment:
                if ch == "\n":
                    comment = False
                continue
            if quote is not None:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    quote = None
                continue
            if ch == "-" and text[i:i+2] == "--":
                comment = True
                continue
            if ch in "'\"":
                quote = ch
                continue
            if ch == "{":
                depth += 1
                if depth == 2:
                    entry_start = i
            elif ch == "}":
                if depth == 2 and entry_start is not None:
                    yield text[entry_start:i+1]
                depth -= 1
                if depth == 0:
                    break
def val(s, name):
    m = field_pattern(name).search(s)
    return int(m.group(1)) if m else 0
def drop_vec(row):
    return row.get("dropVec") or []
def positive_leaf(value):
    try:
        if value is None:
            return False
        if isinstance(value, int):
            return value > 0
        a = str(value).split(";")
        return float(a[-1]) > 0 and float(a[0]) >= 0
    except Exception:
        return False

excel = read_json(ROOT / "ExcelBinOutput/GadgetExcelConfigData.json", [])
if isinstance(excel, dict):
    excel = next((v for v in excel.values() if isinstance(v, list)), [])
gd = {}
for row in excel:
    if not isinstance(row, dict):
        continue
    try:
        gd[int(row.get("id", 0))] = str(row.get("type", row.get("gadgetType", "")))
    except (TypeError, ValueError):
        pass
print("GADGET_TABLE", len(gd), "types", collections.Counter(gd.values()).most_common(18))

table = {}
for filename in ("DropTableExcelConfigData.json", "DropSubTableExcelConfigData.json"):
    entries = read_json(DROP_ROOT / filename, [])
    if not isinstance(entries, list):
        print("UNEXPECTED DROP FORMAT", filename, type(entries).__name__)
        continue
    n = len(entries)
    for row in entries:
        if isinstance(row, dict) and row.get("id") is not None:
            table[int(row["id"])] = row
    print("DROP_TABLE", filename, n)
print("DROP_ROWS_EFFECTIVE", len(table))

chest_list = read_json(SERVER / "ChestDrop.json", [])
chest_tags = collections.defaultdict(list)
for row in chest_list:
    if row.get("index"):
        chest_tags[row["index"]].append(row)
for tag in chest_tags:
    chest_tags[tag].sort(key=lambda x: x.get("minLevel", 0))
print("CHEST_TAG_CONFIG", len(chest_list), "rows", len(chest_tags), "tags")

memo = {}
def structural(root, active=None):
    if root in memo:
        return memo[root]
    if root not in table:
        return "missing"
    if active is None:
        active = set()
    if root in active:
        return "cycle"
    if len(active) >= 80:
        return "too-deep"
    row = table[root]
    entries = [e for e in drop_vec(row) if isinstance(e, dict) and
               int(e.get("weight") or 0) > 0 and
               int(e.get("itemId", e.get("id", 0)) or 0) > 0]
    if not entries:
        return "empty"
    active.add(root)
    problems = []
    valid = 0
    for e in entries:
        leaf = int(e.get("itemId", e.get("id", 0)))
        if not positive_leaf(e.get("countRange")):
            problems.append("bad-count")
        elif leaf in table:
            result = structural(leaf, active)
            if result == "ok":
                valid += 1
            else:
                problems.append("nested-" + result)
        else:
            valid += 1
    active.remove(root)
    result = "ok" if valid > 0 and not problems else (
        "partial" if valid > 0 else (problems[0] if problems else "empty"))
    memo[root] = result
    return result

def resolve(rec):
    # Mirrors ChestRewardSource: explicit ID takes priority; tags are never a
    # silent fallback for an invalid explicit ID.
    if rec["id"] > 0:
        return ("explicit_id", rec["id"], structural(rec["id"]))
    if rec["tag"]:
        options = [r for r in chest_tags.get(rec["tag"], []) if
                   int(r.get("minLevel") or 0) > 0 and
                   int(r.get("minLevel") or 0) <= max(1, rec["level"])]
        if options:
            root = int(options[-1]["dropId"])
            return ("drop_tag", root, structural(root))
        return ("drop_tag", 0, "tag-unmatched")
    return ("none", 0, "no-metadata")

records = []
totals = collections.Counter()
no_gadget = collections.Counter()
types = collections.Counter()
for file in SCENES.rglob("*.lua"):
    totals["script_files"] += 1
    m = scene_pattern.search(file.name)
    scene = m.group(1) if m else file.parent.name
    try:
        content = file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file.read_text(encoding="utf-8", errors="replace")
        totals["bad_encoding_scripts"] += 1
    for fragment in gadget_objects(content):
        gid = val(fragment, "gadget_id")
        if not gid:
            continue
        totals["all_script_gadgets"] += 1
        gtype = gd.get(gid)
        if not gtype:
            no_gadget[gid] += 1
        # Only actual GadgetExcel-configured chests enter the denominator.
        if not gtype or "chest" not in gtype.lower():
            continue
        totals["typed_chests"] += 1
        types[gtype] += 1
        if re.search(r"\bboss_chest\s*=", fragment):
            totals["boss_chests_excluded"] += 1
            continue
        tag_m = tag_pattern.search(fragment)
        tag = tag_m.group(1) if tag_m else ""
        rec = {"scene": scene, "file": str(file), "gadget": gid,
               "config": val(fragment, "config_id"),
               "id": val(fragment, "chest_drop_id"),
               "tag": tag, "level": val(fragment, "level"),
               "drop_count": val(fragment, "drop_count"),
               "oneoff": bool(re.search(r"\bisOneoff\s*=\s*true\b", fragment)),
               "persistent": bool(re.search(r"\bpersistent\s*=\s*true\b",fragment))}
        records.append(rec)

totals["ordinary_chests"] = len(records)
by_source = collections.Counter()
by_status = collections.Counter()
by_scene = collections.defaultdict(collections.Counter)
failures = collections.defaultdict(list)
problem_roots = collections.Counter()
for rec in records:
    source, root, status = resolve(rec)
    by_source[source] += 1
    by_status[status] += 1
    by_scene[rec["scene"]]["total"] += 1
    by_scene[rec["scene"]][source] += 1
    by_scene[rec["scene"]][status] += 1
    if status != "ok":
        problem_roots[(source, root, status)] += 1
        if len(failures[status]) < 15:
            failures[status].append({**rec, "root": root, "source": source})
print("SCENE_SCRIPTS_SCANNED", totals["script_files"])
print("ALL_SCENE_GADGETS", totals["all_script_gadgets"])
print("TYPED_CHESTS", totals["typed_chests"], "BOSS_EXCLUDED", totals["boss_chests_excluded"])
print("NORMAL_CHESTS", totals["ordinary_chests"])
print("SOURCE", json.dumps(by_source, ensure_ascii=False))
print("RESOLUTION", json.dumps(by_status, ensure_ascii=False))
if records:
    resolved = by_status["ok"]
    print("STRUCTURAL_COVERAGE_PERCENT", round(100 * resolved / len(records), 3))
print("BY_SCENE", json.dumps(
    sorted(({**{"scene": k}, **v} for k,v in by_scene.items()),
           key=lambda row: -row["total"])[:55], ensure_ascii=False))
print("TOP_MISSING_ROOTS", json.dumps(problem_roots.most_common(40), ensure_ascii=False))
print("MISSING_GADGET_EXCEL_ID", sum(no_gadget.values()), "top", no_gadget.most_common(20))
print("TYPES", types.most_common(20))
print("SAMPLES", json.dumps(failures, ensure_ascii=False))
native_ids = {r["id"] for r in records if r["id"] > 0}
tag_names = {r["tag"] for r in records if r["tag"]}
print("NATIVE_CHEST_IDS_UNIQUE", len(native_ids))
print("UNIQUE_TAGS_USED", len(tag_names))
print("UNKNOWN_TAGS", sorted(tag_names - chest_tags.keys())[:100])
print("UNREFERENCED_TAGS", len(chest_tags.keys() - tag_names))
for p in ("nodkrai_explore_points.json", "snezhnaya_explore_points.json", "region_explore_points.json"):
    data = read_json(SERVER / p)
    if data is None:
        continue
    if isinstance(data, list):
        kinds = collections.Counter(str(x.get("kind", "")) for x in data if isinstance(x, dict))
        print("SYNTHETIC", p, "rows", len(data), "chests", sum(v for k,v in kinds.items() if k.startswith("chest")), "kinds", kinds.most_common(24))
    elif isinstance(data, dict):
        print("SYNTHETIC", p, "top_keys", list(data)[:25], "counts", {k:len(v) for k,v in data.items() if isinstance(v, list)})
report = {"resource_source": "MeChen618/AstaPS-Resource@85b81a69",
          "server_source": "MeChen618/AstaPS@dcf04369",
          "notes": ["Structural payload validity only; item ID/economy/rarity authenticity not verified",
                    "Includes only GadgetExcel-defined Chest gadgets in Scripts/Scene",
                    "Quest-created and synthetic chests are separate populations"],
          "totals": dict(totals), "source": dict(by_source),
          "result": dict(by_status), "by_scene": {k:dict(v) for k,v in by_scene.items()},
          "top_problem_roots": [[list(k),v] for k,v in problem_roots.most_common(100)],
          "samples": dict(failures)}
Path("chest-coverage-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

# Root-level and immediate-child diagnostics for common partial and empty outcomes.
for root in (1000100, 52040000, 52030000, 52020500, 51040000, 51010000, 51010500):
    row = table.get(root)
    if row is None:
        continue
    vec = drop_vec(row)
    print("ROOT_PROBE", root, "status", structural(root), "vec", len(vec),
          "randomType", row.get("randomType"), "nodeType", row.get("nodeType"),
          "first_entries", json.dumps(vec[:8],ensure_ascii=False))
    children = [int(e.get("itemId",0)) for e in vec if isinstance(e,dict)
                and int(e.get("itemId") or 0) in table]
    for child in children[:3]:
        childrow = table[child]
        print("  CHILD", child, "status", structural(child),
              "count", len(drop_vec(childrow)), "items",
              json.dumps(drop_vec(childrow)[:6],ensure_ascii=False))
# Break down omissions by source and by scene, including the original one-off policy.
for scope, rows in (("all",records),("scene3",[r for r in records if r["scene"] == "3"]),
                    ("oneoff",[r for r in records if r["oneoff"]])):
    statuses = collections.Counter(resolve(r)[2] for r in rows)
    sources = collections.Counter(resolve(r)[0] for r in rows)
    print("SCOPE",scope,"n",len(rows),"source",json.dumps(sources),
          "status",json.dumps(statuses))

def min_count_at_least_one(value):
    if value is None:
        return False
    try:
        s = str(value).split(";")[0]
        return float(s) >= 1
    except (TypeError, ValueError):
        return False
def has_guaranteed_leaf(root, active=None):
    if root not in table:
        return False
    if active is None:
        active = set()
    if root in active or len(active) > 80:
        return False
    row = table[root]
    vec = [e for e in drop_vec(row) if isinstance(e, dict)
           and int(e.get("weight") or 0) > 0 and int(e.get("itemId") or 0) > 0]
    if not vec:
        return False
    active.add(root)
    def always(item):
        child_id = int(item.get("itemId"))
        if not min_count_at_least_one(item.get("countRange")):
            return False
        if child_id in table:
            return has_guaranteed_leaf(child_id, active)
        return True
    if row.get("randomType") == 1:
        result = any(int(e.get("weight") or 0) >= 10000 and always(e) for e in vec)
    elif row.get("randomType") == 0:
        result = all(always(e) for e in vec)
    else:
        result = False
    active.remove(root)
    return result

for scope, rows in (("scene_all",records),
                    ("isOneoff_true",[r for r in records if r["oneoff"]]),
                    ("persistent_true",[r for r in records if r["persistent"]]),
                    ("both_flags_false",[r for r in records if not r["oneoff"] and not r["persistent"]]),
                    ("scene3_oneoff",[r for r in records if r["scene"] == "3" and r["oneoff"]])):
    summary=collections.Counter()
    for rec in rows:
        source,root,status = resolve(rec)
        summary["total"] += 1
        summary["metadata"] += source != "none"
        summary["structural_ok"] += status == "ok"
        summary["structural_partial"] += status == "partial"
        summary["guaranteed_native_leaf"] += (root > 0 and has_guaranteed_leaf(root))
        summary["no_metadata"] += status == "no-metadata"
        summary["missing_root"] += status == "missing"
        summary["empty_root"] += status == "empty"
    print("GUARANTEE_SCOPE",scope,json.dumps(summary))
