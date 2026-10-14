#!/usr/bin/env python3
"""Audit all scripted 7.1 chests: geographic area_id against reward drop_tag.

Read only resource files. Region truth: CityConfigData.areaIdVec, never drop_tag.
Output is a summary plus examples; does not alter loot or resource contents.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "ScriptSceneData/flat.luas.scenes.full_globals.lua.json"
CITY = ROOT / "ExcelBinOutput/CityConfigData.json"
GADGET = ROOT / "ExcelBinOutput/GadgetExcelConfigData.json"
NAME_BY_CITY = {
  1: "蒙德", 2: "璃月", 3: "稻妻", 4: "须弥", 5: "枫丹", 6: "纳塔",
  7: "挪德卡莱", 8: "至冬", 9: "至冬", 99: "璃月", 100: "璃月",
  101: "璃月", 102: "璃月", 103: "璃月", 104: "璃月",
  105: "天穹",
}
COUNTRIES = ("挪德卡莱", "诺德克莱", "蒙德", "璃月", "稻妻", "须弥",
             "枫丹", "纳塔", "至冬", "群岛")
NORMALIZED = {"诺德克莱": "挪德卡莱"}
PREFAB = re.compile(r"^SceneObj_Chest_(?:Default|Locked|Bramble|Frozen)_Lv[1245](?:_(?:UnderWater|AboveWater|Amphibious|V70|RemusLanternFish|FollowMove))?$")
REGULAR_TAG = re.compile(r"^(?:雪山)?(?:战斗|解谜)(?:低级|中级|高级|超级)")
MAX_SAMPLES = 12

def area_region(x, by_area):
    try:
        return by_area.get(int(x))
    except (TypeError, ValueError):
        return None

def tag_region(tag):
    if not isinstance(tag, str):
        return None
    for v in COUNTRIES:
        if tag.endswith(v):
            return NORMALIZED.get(v, v)
    return None

def run():
    city = json.loads(CITY.read_text(encoding="utf-8"))
    by_area, ambiguous = {}, collections.defaultdict(set)
    for record in city:
        region = NAME_BY_CITY.get(record.get("cityId"))
        if not region:
            continue
        for id_ in record.get("areaIdVec", []):
            if id_ in by_area and by_area[id_] != region:
                ambiguous[id_].update((by_area[id_], region))
            by_area[id_] = region
    print("AREA_MAP", json.dumps(by_area, ensure_ascii=False, sort_keys=True), flush=True)
    print("AREA_CONFLICTS", dict(ambiguous), flush=True)
    print("INPUT_FILE_SIZES", {"scenes": SCENE.stat().st_size,
                               "gadget": GADGET.stat().st_size}, flush=True)

    gadgets = json.loads(GADGET.read_text(encoding="utf-8"))
    print("GADGET_EXAMPLE", json.dumps(gadgets[:2], ensure_ascii=False)[:1500], flush=True)
    by_gid = {}
    for item in gadgets:
        gid = item.get("id", item.get("gadgetId"))
        if gid is None: continue
        by_gid[int(gid)] = item
    print("GADGETS_INDEXED", len(by_gid), flush=True)

    with SCENE.open(encoding="utf-8") as handle:
        data = json.load(handle)
    print("SCENE_ROOT", type(data).__name__, list(data)[:8] if isinstance(data, dict) else len(data), flush=True)

    found=0
    objects=0
    tag_count=collections.Counter()
    by_kind=collections.Counter()
    pair=collections.Counter()
    area_only=collections.Counter()
    mismatches=[]
    unknown_area=[]
    missing_tag=[]
    known_match=collections.Counter()
    tag_to_area=collections.Counter()
    area_to_tag=collections.Counter()
    sample_any=[]
    examples_by_region=collections.defaultdict(list)
    shape=collections.Counter()

    def visit(node, path=()):
        nonlocal found, objects
        if isinstance(node, dict):
            objects += 1
            if "gadget_id" in node or "drop_tag" in node:
                found += 1
                tag=node.get("drop_tag")
                aid=node.get("area_id")
                gid=node.get("gadget_id")
                src=by_gid.get(int(gid), {}) if str(gid).isdigit() else {}
                prefab=src.get("jsonName") or src.get("json_name") or src.get("name") or ""
                gadget_type=src.get("type")
                likely_chest=bool(
                    PREFAB.fullmatch(prefab) or
                    (str(gadget_type).lower() == "chest") or
                    (tag and (REGULAR_TAG.match(str(tag)) or "灵龛" in str(tag) or "宝箱" in str(tag)))
                )
                if not likely_chest:
                    shape["other_gadgets"]+=1
                else:
                    shape["chests"] += 1
                    source_region=area_region(aid,by_area)
                    labeled_region=tag_region(tag)
                    source_region=source_region or "unknown_area"
                    labeled_region=labeled_region or "no_region_tag"
                    shape["quality_eligible_prefab"]+=bool(PREFAB.fullmatch(prefab))
                    pair[(source_region,labeled_region)] += 1
                    area_only[source_region]+=1
                    tag_count[labeled_region]+=1
                    by_kind[str(gadget_type)]+=1
                    sample={"file":"/".join(map(str,path[-5:])), "config_id":node.get("config_id"),
                            "gadget_id":gid, "prefab":prefab,
                            "area_id":aid,"area":source_region,"tag":tag,"tagArea":labeled_region,
                            "position":node.get("pos")}
                    if len(sample_any)<5: sample_any.append(sample)
                    if labeled_region != "no_region_tag":
                        tag_to_area[labeled_region]+=1
                    if source_region != "unknown_area":
                        area_to_tag[source_region]+=1
                    if source_region != "unknown_area" and labeled_region != "no_region_tag":
                        if source_region==labeled_region: known_match[source_region]+=1
                        elif len(mismatches)<MAX_SAMPLES: mismatches.append(sample)
                    elif source_region == "unknown_area" and len(unknown_area)<MAX_SAMPLES:
                        unknown_area.append(sample)
                    elif labeled_region=="no_region_tag" and len(missing_tag)<MAX_SAMPLES:
                        missing_tag.append(sample)
                    if len(examples_by_region[source_region])<2:
                        examples_by_region[source_region].append(sample)
            for k,v in node.items():
                if isinstance(v,(dict,list)):
                    visit(v,path+(str(k),))
        elif isinstance(node, list):
            for i,v in enumerate(node):
                if isinstance(v,(dict,list)):
                    visit(v,path+(str(i),))

    visit(data)
    report = {
        "nodesWalked":objects, "candidateGadgets":found, "shapes":dict(shape),
        "pairs":sorted([{"area":area,"tagRegion":tag,"count":count}
                       for (area,tag),count in pair.items()],
                       key=lambda d:(d["area"],d["tagRegion"])),
        "byArea":dict(area_only), "byTag":dict(tag_count),
        "exactMatches":dict(known_match),
        "withRegionTag":dict(tag_to_area), "withKnownArea":dict(area_to_tag),
        "mismatchExamples":mismatches,
        "unknownAreaExamples":unknown_area,
        "missingTagExamples":missing_tag,
        "sampleAny":sample_any,
        "examplePerArea":dict(examples_by_region),
    }
    print("AUDIT_REPORT_JSON_BEGIN", flush=True)
    print(json.dumps(report,ensure_ascii=False,separators=(",",":")),flush=True)
    print("AUDIT_REPORT_JSON_END", flush=True)
    if found==0 or shape["chests"]==0:
        raise SystemExit("ERROR: no chest records extracted; revise flattened scene schema")
if __name__ == "__main__":
    run()
