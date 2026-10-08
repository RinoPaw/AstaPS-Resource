#!/usr/bin/env python3
"""Static 7.1 Mondstadt prologue audit; no assertion of playable client behavior.

Provenance:
- Native full Quest: RinoPaw/Genshin-Reverse, quest-extraction analysis.
- Historical compatibility beginExec: TomyJan/GCResource 3700 and 4000.
- Native 7.1 scene Lua: this repository, Scripts/Scene.
- Scope: prelude, Prologue Acts I/II/III; see Genshin-Reverse mainline manifest.
"""
import json
import re
from pathlib import Path

SCOPE = {
    "prelude": (351, 359, 361),
    "act1": (363, 352, 353, 355, 354, 360, 356, 357, 358, 306, 307, 308, 309, 311),
    "act2": (370, 371, 372, 373, 374, 375, 376, 377, 20101, 379, 380, 381, 382, 383, 384),
    "act3": (397, 388, 389, 390, 393, 394, 398, 396),
}
# Only narrowly confirmed historical actions are asserted. Empty modern beginExec
# is NOT automatically treated as broken: some actions moved to other assets.
ACTIONS = {
    35301: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003002,1"]),
    35302: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003002,2"]),
    35303: ("beginExec", "QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003448"]),
    35304: ("beginExec", "QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003449"]),
    35404: ("beginExec", "QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003439"]),
    36001: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003435,1"]),
    36003: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003136,1"]),
    35901: ("beginExec", "QUEST_EXEC_SET_WEATHER_GADGET", ["3", "1"]),
    30904: ("beginExec", "QUEST_EXEC_ADD_QUEST_PROGRESS", ["359011", "1"]),
    37303: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133001305,2"]),
    2010102: ("beginExec", "QUEST_EXEC_GRANT_TRIAL_AVATAR", ["11"]),
    38202: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133001249,2"]),
    39703: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133002233,2"]),
    38905: ("beginExec", "QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133007227"]),
    39003: ("beginExec", "QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133007227"]),
    39401: ("beginExec", "QUEST_EXEC_UNLOCK_POINT", ["3", "38"]),
    39801: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133003910,2"]),
    39808: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133004917,1"]),
    39812: ("beginExec", "QUEST_EXEC_NOTIFY_GROUP_LUA", ["3", "133003910"]),
    39604: ("beginExec", "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133001910,2"]),
}
COMBINATORS = {31101: "LOGIC_OR", 35901: "LOGIC_OR"}
CHAPTER_BEGIN = {1001: 36301, 1002: 37004, 1003: 39705}
CHAPTER_END = {1001: 31101, 1002: 38406, 1003: 39604}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(test, message):
    if not test:
        raise AssertionError(message)


def expected_action(row, field, action_type, params):
    return {"type": action_type, "param": params} in [
        {"type": x.get("type"), "param": x.get("param")}
        for x in row.get(field, [])
    ]


def has_condition(row, typ, first, second=None):
    return any(
        c.get("type") == typ
        and c.get("param", [None])[0] == first
        and (second is None or len(c.get("param", [])) > 1 and c["param"][1] == second)
        for c in row.get("acceptCond", [])
    )


def lua(group):
    path = Path("Scripts/Scene/3/scene3_group%d.lua" % group)
    require(path.is_file(), "Missing group Lua: %s" % path)
    text = path.read_text(encoding="utf-8")
    require("group_id = %d" % group in text, "Wrong group identity %d" % group)
    return text


def check_scene(scripts):
    a = lua(133003002)
    require(re.search(r"monsters\s*=\s*\{\s*439\s*\}", a), "35302 slime suite absent")
    require('ScriptLib.AddQuestProgress(context, "1330030022")' in a, "35302 kill notification missing")
    # Later tutorial waves are quest-start-triggered: the task must emit the
    # Lua event, which in turn creates the actual world monsters.
    for sub, gid, monster_configs, progress in [
        (35303, 133003448, (440, 441), "1330030023"),
        (35304, 133003449, (442, 443, 444, 445), "1330030024"),
    ]:
        group_lua = lua(gid)
        require('source = "%d"' % sub in group_lua,
                "Quest %d has no Lua QUEST_START trigger" % sub)
        for config in monster_configs:
            require(re.search(
                r"ScriptLib\.CreateMonster\(context,\s*\{\s*config_id\s*=\s*%d\b" % config,
                group_lua,
            ), "Quest %d cannot create tutorial slime config %d" % (sub, config))
        require('ScriptLib.AddQuestProgress(context, "%s")' % progress in group_lua,
                "Quest %d wave has no completion Lua progress" % sub)

    a = lua(133003439)
    for token in ('source = "35404"', 'config_id = 3834',
                  'ScriptLib.CreateGadget(context, { config_id = 3834 })',
                  'ScriptLib.AddQuestProgress(context, "133003079")'):
        require(token in a, "35404 moving target lacks " + token)
    for gid, configs, progress in [
        (133003435, (1442,), "133003435"),
        (133003136, (623, 1443, 1444), "133003136"),
    ]:
        a = lua(gid)
        first = re.search(r"suites\s*=\s*\{\s*\{(.*?)\}\s*,", a, re.S)
        require(first is not None, "No initial suite in group %d" % gid)
        for config in configs:
            require(re.search(r"\b%d\b" % config, first.group(1)),
                    "Group %d suite 1 missing monster %d" % (gid, config))
        require('ScriptLib.AddQuestProgress(context, "%s")' % progress in a,
                "Group %d missing quest progress trigger" % gid)
    scripts.add("353 first/second/third slime waves, 354 target, 360 hilichurl groups")


def check_act23_resources():
    routes = load("BinOutput/LevelDesign/Routes/scene20023_routes.json")
    require(routes.get("sceneId") == 20023, "Act II elevator route scene mismatch")
    require(any(x.get("localId") == 3 for x in routes.get("routes", [])),
            "Act II hideout elevator route 3 absent")
    keep = Path("Scripts/Scene/20017/scene20017_block20017.lua").read_text(encoding="utf-8")
    require("220017001" in keep and "dontUnload = true" in keep,
            "Act III Stormterror scene group lifetime not retained")
    for scene in (20017, 20018, 20020):
        s = Path("Scripts/Scene/%d/scene%d_group2200%d001.lua" % (scene, scene, scene % 100)).read_text(encoding="utf-8")
        require("special_name_id = 2010102" in s,
                "Stormterror scene %d missing corrected displayed name" % scene)
    for gid in (133007228, 133007229, 133007230):
        text = lua(gid)
        require("Point_Value" in text and "Temp_Point_Value" in text,
                "Tower seal %d lacks collection/delivery state" % gid)
    final = lua(133007230)
    require("seal_battle_done" in final, "Third seal missing battle-complete guard")


def check_reviewed_later_acts(subs):
    require(expected_action(subs[2010101], "beginExec",
                            "QUEST_EXEC_DEL_PACK_ITEM", ["100175", "1"]),
            "2010101 must consume the hideout key")
    require(expected_action(subs[2010101], "beginExec",
                            "QUEST_EXEC_REFRESH_GROUP_SUITE", ["3", "133002334,2"]),
            "2010101 must activate hideout gadget group")
    require(expected_action(subs[2010151], "finishExec",
                            "QUEST_EXEC_REMOVE_TRIAL_AVATAR", ["11"]),
            "2010102 trial avatar must be revoked on dungeon exit")
    require(expected_action(subs[38402], "failExec",
                            "QUEST_EXEC_ROLLBACK_QUEST", ["38401"]),
            "38402 failure must enable retry")
    reward_ids = {37203: 100164, 38303: 100163, 38406: 100165}
    reward_ids.update({sub: 100175 for sub in (
        2010145, 2010146, 2010147, 2010148, 2010149, 2010150, 2010151)})
    for sub, item in reward_ids.items():
        require(subs[sub].get("gainItems") == [{"itemId": item, "count": 1}],
                "Missing quest reward %d in %d" % (item, sub))
    for gid, tokens in {
        133001305: ("monsters = { 1307 }",),
        133002334: ("gadgets = { 334001 }",),
        133001249: ("gadgets = { 2883 }",),
        133002233: ("monsters = { 870, 871, 872 }",),
        133007227: ('source = "38905"', 'source = "39003"',
                      'AddQuestProgress(context, "39003_success")'),
        133003910: ('source = "39812"', 'AddQuestProgress(context, "133003910")'),
        133004917: ("suites = {",),
        133001910: ("gadgets = { 910001 }",),
    }.items():
        lua_content = lua(gid)
        for token in tokens:
            require(token in lua_content,
                    "Group %d lacks evidence token: %s" % (gid, token))


def main():
    mains, subs, count = {}, {}, 0
    for chapter, ids in SCOPE.items():
        for main_id in ids:
            path = Path("BinOutput/Quest/%d.json" % main_id)
            require(path.is_file(), "Missing %s MainQuest %d" % (chapter, main_id))
            obj = load(path)
            require(obj.get("id") == main_id, "MainQuest identity mismatch: %d" % main_id)
            rows = obj.get("subQuests")
            require(isinstance(rows, list) and rows, "Empty quest %d" % main_id)
            mains[main_id] = obj
            for row in rows:
                sub = row["subId"]
                require(sub not in subs, "Duplicate subquest %d" % sub)
                require(row.get("mainId") == main_id, "Bad parent for %d" % sub)
                subs[sub] = row
                count += 1
                for field in ("finishCond", "failCond", "finishExec", "failExec", "beginExec"):
                    for entry in row.get(field, []):
                        require(isinstance(entry.get("type"), str),
                                "Unnamed %s for %d" % (field, sub))
            print("%s: %d main quests" % (chapter, len(ids)))
    for sub, (field, kind, params) in ACTIONS.items():
        require(sub in subs and expected_action(subs[sub], field, kind, params),
                "Lost reviewed compatibility %d %s %s" % (sub, field, kind))
    for sub, logic in COMBINATORS.items():
        require(subs[sub].get("finishCondComb") == logic, "%d must combine finish with %s" % (sub, logic))
    require(not any(x.get("type") == "QUEST_EXEC_GRANT_TRIAL_AVATAR"
                    for x in subs[35301].get("finishExec", [])),
            "35301 incorrectly grants Amber before Anemo tutorial")
    require(subs[35402].get("gainItems") == [{"itemId": 1021, "count": 1}],
            "35402 must give Amber's encounter reward")
    require(expected_action(subs[35304], "beginExec",
                            "QUEST_EXEC_ADD_CUR_AVATAR_ENERGY", []),
            "35304 needs elemental burst energy during third slime wave")
    for sub, progress in ((35309, "1330030022"),
                          (35310, "1330030023"),
                          (35311, "1330030024")):
        require(any(c.get("type") == "QUEST_CONTENT_LUA_NOTIFY"
                    and c.get("param_str") == progress
                    for c in subs[sub].get("finishCond", [])),
                "Quest %d is disconnected from slime wave %s" % (sub, progress))
    require(has_condition(subs[36301], "QUEST_COND_STATE_EQUAL", 35202, 3),
            "Chapter 1001 must open only after 35202")
    for chapter, sub in CHAPTER_BEGIN.items():
        require(sub in subs, "Missing chapter %d opener %d" % (chapter, sub))
    for chapter, sub in CHAPTER_END.items():
        require(sub in subs, "Missing chapter %d closer %d" % (chapter, sub))
    for chapter, ids in SCOPE.items():
        if chapter in ("act1", "act2", "act3"):
            require(all(mains[q].get("series") in (1001, 1002, 1003) for q in ids),
                    "Unexpected chapter series in %s" % chapter)
    # Detect current Excel priority conflicts on repaired beginExec/actions.
    excel_path = Path("ExcelBinOutput/QuestExcelConfigData.json")
    if excel_path.exists():
        rows = {r.get("subId"): r for r in load(excel_path) if isinstance(r, dict)}
        for sub, (field, kind, params) in ACTIONS.items():
            if sub not in rows:
                continue
            actions = [e for e in rows[sub].get(field, []) if e.get("type")]
            if actions:
                require(expected_action(rows[sub], field, kind, params),
                        "QuestExcel nonempty %d %s masks BinOutput action" % (sub, field))
        require(not any(x.get("type") == "QUEST_EXEC_GRANT_TRIAL_AVATAR"
                        for x in rows.get(35301, {}).get("finishExec", [])),
                "QuestExcel prematurely grants trial Amber")
    scripts = set()
    check_scene(scripts)
    check_act23_resources()
    check_reviewed_later_acts(subs)
    print("PASS static Mondstadt prologue: %d main quests, %d subquests, "
          "%d reviewed actions; %s" %
          (len(mains), count, len(ACTIONS), ", ".join(sorted(scripts))))
    print("NOTE: does not prove chapter gameplay, scene lifecycle, or old save recovery")


if __name__ == "__main__":
    main()
