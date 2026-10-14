#!/usr/bin/env python3
"""Cross-check scene-group chest region labels against independently configured area IDs.

Only files in Scripts/Scene for open-world scenes are scanned, not the older flat
Lua snapshot. No loot values are changed. Export anomalous rows in audit-results/.
"""
import collections
import csv
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
SCENES=(1,3,4,5,6,7,9,10,11)
CITY_IDS={1:"蒙德",2:"璃月",3:"稻妻",4:"须弥",5:"枫丹",6:"纳塔",7:"挪德卡莱",
          8:"至冬",9:"至冬",99:"璃月",100:"璃月",101:"璃月",102:"璃月",
          103:"璃月",104:"璃月",105:"天穹"}
COUNTRIES=("挪德卡莱","诺德克莱","蒙德","璃月","稻妻","须弥","枫丹","纳塔","至冬","群岛")
PREFAB=re.compile(r"^SceneObj_Chest_(?:(?:Default|Locked|Bramble|Frozen)_Lv[1245](?:_(?:UnderWater|AboveWater|Amphibious|V70|RemusLanternFish|FollowMove))?|Rock_Lv1)$")
ID=re.compile(r"\bconfig_id\s*=\s*(\d+)")
GID=re.compile(r"\bgadget_id\s*=\s*(\d+)")
AREA=re.compile(r"\barea_id\s*=\s*(\d+)")
TAG=re.compile(r'\bdrop_tag\s*=\s*["\x27]([^"\x27]+)["\x27]')
POS=re.compile(r'\bpos\s*=\s*\{[^}]*\bx\s*=\s*([-\d.]+)[^}]*\by\s*=\s*([-\d.]+)[^}]*\bz\s*=\s*([-\d.]+)')
ROOT=BASE/"audit-results"

def norm(name):
    return "挪德卡莱" if name=="诺德克莱" else name

def suffix(tag):
    for name in COUNTRIES:
        if tag.endswith(name): return norm(name)
    return None

def run():
    by_area={}
    for entry in json.loads((BASE/"ExcelBinOutput/CityConfigData.json").read_text()):
        name=CITY_IDS.get(entry.get("cityId"))
        if name:
            for area in entry.get("areaIdVec",[]):
                by_area[area]=name
    gadget_rows=json.loads((BASE/"ExcelBinOutput/GadgetExcelConfigData.json").read_text())
    gadgets={row["id"]:row for row in gadget_rows if "id" in row}
    stat=collections.Counter()
    pairs=collections.Counter()
    tags=collections.Counter()
    areas=collections.Counter()
    by_scene=collections.Counter()
    special=collections.Counter()
    samples=collections.defaultdict(list)
    results=[]
    def sample(key,row):
        if len(samples[key])<8: samples[key].append({k:row.get(k) for k in ("scene","path","config","gid","prefab","area_id","areaRegion","tag","tagRegion","pos")})

    for scene in SCENES:
        files=sorted((BASE/f"Scripts/Scene/{scene}").glob(f"scene{scene}_group*.lua"))
        stat[f"scene{scene}_files"]=len(files)
        for path in files:
            for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
                if "gadget_id" not in line or "config_id" not in line:
                    continue
                config=ID.search(line);gid=GID.search(line)
                if not config or not gid: continue
                info=gadgets.get(int(gid.group(1)),{})
                prefab=info.get("jsonName","")
                ctype=info.get("type","")
                ordinary=bool(PREFAB.fullmatch(prefab))
                chest=bool(prefab.startswith("SceneObj_Chest_"))
                if not chest and ctype!="Chest":continue
                aid=AREA.search(line);tag=TAG.search(line);pos=POS.search(line)
                area_id=int(aid.group(1)) if aid else None
                # The 100-103 CityConfigData entries are reused by the Golden
                # Apple Archipelago (scene 4), and are NOT mainland Liyue.
                region="群岛" if scene==4 else by_area.get(area_id)
                tag_txt=tag.group(1) if tag else ""
                label=suffix(tag_txt)
                row={
                    "scene":scene,"path":str(path.relative_to(BASE)),"config":int(config.group(1)),
                    "gid":int(gid.group(1)),"prefab":prefab,"chestType":ctype,
                    "area_id":area_id,"areaRegion":region or "",
                    "tag":tag_txt,"tagRegion":label or "",
                    "pos":",".join(pos.groups()) if pos else "",
                    "ordinary":ordinary
                }
                results.append(row)
                stat["chest_like_all"]+=1
                if not ordinary:
                    stat["other_chest_like"]+=1
                    continue
                stat["ordinary"]+=1
                by_scene[scene]+=1
                area=region or "UNKNOWN_AREA"
                tagged=label or "NO_REGION_TAG"
                pairs[(area,tagged)]+=1
                tags[tagged]+=1
                areas[area]+=1
                if not region: sample("unknown_area",row)
                elif not label: sample("missing_tag",row)
                elif region!=label: sample("wrong_tag",row)
                else: stat["exact_matches"]+=1
                if tag_txt.startswith("雪山"): special[(region or "UNKNOWN_AREA",tagged)]+=1
    ROOT.mkdir(exist_ok=True)
    with (ROOT/"all-chests.csv").open("w",newline="",encoding="utf-8-sig") as fp:
        fields=["scene","path","config","gid","prefab","chestType","area_id",
                "areaRegion","tag","tagRegion","pos","ordinary"]
        w=csv.DictWriter(fp,fieldnames=fields)
        w.writeheader();w.writerows(results)
    with (ROOT/"exceptions.csv").open("w",newline="",encoding="utf-8-sig") as fp:
        w=csv.DictWriter(fp,fieldnames=fields);w.writeheader()
        w.writerows(x for x in results if x["ordinary"] and x["areaRegion"]!=x["tagRegion"])
    summary={
        "stats":dict(stat),"byScene":dict(by_scene),"byArea":dict(areas),"byTag":dict(tags),
        "pairs":[{"area":a,"tag":t,"count":n} for (a,t),n in sorted(pairs.items())],
        "snowMountain":[{"area":a,"tag":t,"count":n} for (a,t),n in sorted(special.items())],
        "examples":dict(samples),"csvRows":len(results),
        "method":"Scripts/Scene scene*_group*.lua gadget_id -> GadgetExcel prefab; independent CityConfig.areaIdVec + scene 4=archipelago"
    }
    (ROOT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SCENE_AUDIT_JSON_BEGIN",flush=True)
    print(json.dumps(summary,ensure_ascii=False,separators=(",",":")),flush=True)
    print("SCENE_AUDIT_JSON_END",flush=True)
    if not stat["ordinary"]:raise SystemExit("No ordinary chests found; input or parser failure")
if __name__=="__main__":
    run()
