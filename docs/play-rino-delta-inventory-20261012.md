# play/rino remaining resource delta (2026-10-12)

Read-only static inventory. The comparison uses upstream/fork `main` at `5ff5f0b083fd3683aca894e4ebc2ba602306820f` and archived `play/rino` at `211077dd3e7ea7e89e9cf3e7891b07639b3b3134` (immediately before this report). **Do not deploy or wholesale merge `play/rino`.** No 7.1 client regression tests were performed for these differences.

## Already consolidated

- Chapter 1301 historical evidence and unresolved 7.1-only `300012`: [Genshin-Reverse analysis](https://github.com/RinoPaw/Genshin-Reverse/tree/f075efea9496f84a9d7faafa68d146473aca1f79/versions/7.1.0-global/analyses/quest-prerequisites/chapter1301).
- QuestExcel prerequisite repair: [upstream PR #17](https://github.com/MeChen618/AstaPS-Resource/pull/17), covering 314 existing flattened rows with `acceptCond` and `acceptCondComb` only. It is *not* a verified 7.1 native prerequisite extraction.
- Historical workflows and 20 byte-identical upstream Python repair tools were removed from this branch. Current tools live on upstream `main`.
- `docs/fontaine-weapon-domain-starters-71.md` and `scripts/validate_fontaine_weapon_domains.py` have byte-identical upstream blobs. `ScriptSceneData/`, `Server/`, and `TextMap/` have matching tree SHAs at the checked revisions.

## Changes still specific to the archive

### Quest sources (22 files, 39 modified subquest records)

`BinOutput/Quest/` differs in:
`20101, 307, 308, 309, 311, 353, 354, 359, 360, 372, 373, 376, 382, 383, 384, 388, 389, 390, 394, 396, 397, 398.json`.

All 22 files have the same subquest counts and IDs on both branches. Differences are restricted to individual subquest fields `beginExec`, `finishExec`, `gainItems`, `finishCondComb`, or `failCondComb`; no additional source field families were found. In particular, `play/rino/BinOutput/Quest/353.json` contains a `QUEST_EXEC_GRANT_TRIAL_AVATAR` `finishExec` on subquest `35301` absent from upstream. This old grant is unsafe to replay.

### Flattened Excel and other JSON

- `ExcelBinOutput/QuestExcelConfigData.json`: historical flattened quest variant; do not overwrite the repaired upstream file or reapply obsolete generators.
- `ExcelBinOutput/DungeonExcelConfigData.json`: exactly one row differs, dungeon `id=2001`. Upstream names the 2002 transition `passJumpDungeon`; `play/rino` names it `DBMHBKIDAJH`. Static comparison does not by itself certify either spelling in client runtime.
- `BinOutput/Gadget/ConfigGadget_Npc.json`: `DragonFeather_HP.combat.property.isInvincible` is `false` upstream, `true` in `play/rino`.
- `BinOutput/Ability/Temp/GadgetAbilities/ConfigAbility_Scene_Seal.json`: action parameters and team-level LightLock counter actions differ; the archive includes old `DIEOFOGAIIN` keys.
- `BinOutput/LevelDesign/Routes/scene20023_routes.json` is **present only in upstream main**; it is not a unique archive addition.

### Lua scenes and gadgets

- `Scripts/Gadget/tree.lua`: same script content, different terminal newline.
- `Scripts/Gadget/Test_LightLock.lua`: upstream has additional signal-state handling; archive lacks those 18 lines.
- `Scripts/Scene/20017/scene20017_block20017.lua`: upstream adds `dontUnload = true`.
- `Scripts/Scene/20017/scene20017_group220017001.lua`, `20018/scene20018_group220018001.lua`, `20020/scene20020_group220020001.lua`: historical monster `special_name_id` differences.
- `Scripts/Scene/3/scene3_group133007228.lua`, `133007229.lua`, `133007230.lua`: upstream has later seal state/trigger recovery and related cleanup.

The archived `.gitignore` and archive-oriented `README.md` are branch metadata, not gameplay changes. Upstream CI workflows and verification tools missing from `play/rino` are **not** evidence of archive improvements.

## Branch review and disposition

- `fix/questexcel-verified-special-chapters-71`: final Git tree is identical to `main` at the pinned SHA; redundant as an active branch.
- `fix/questexcel-verified-prereqs-71`: a subset of the merged PR #17; no new production patch needed.
- `audit/rino-questexcel-mainline-71`: older README-only audit branch; upstream README already describes the ownership boundary without its stale link.
- `audit/rino-resource-reconcile-20261012`: the **two unique read-only audit scripts** and reproducibility/CI provenance are now [archived in Genshin-Reverse](https://github.com/RinoPaw/Genshin-Reverse/tree/52fc8cd6bdc61d849f3760070b76173a3cdb34ba/versions/7.1.0-global/analyses/quest-prerequisites/pr17-audit-archive); original workflow files remain linked to their pinned SHA there. Eligible for branch retirement after verifying the remote head.
- `integrate/mondstadt-prologue-71` and `fix/mondstadt-71-rino-compat`: historical compatibility research now [archived with source/tool SHA evidence in Genshin-Reverse](https://github.com/RinoPaw/Genshin-Reverse/tree/628f958aab4a7df9a8ded032e58911225edafad7/versions/7.1.0-global/analyses/quest-prerequisites/mondstadt-prologue). Both are eligible for branch retirement after confirming their exact remote heads; neither has a remaining proven upstream production fix. The older compat branch retains stale `38201` and `39807` OR combinators and the discarded `38402` rollback.
- `rino-native-mainline-quests`: separate experiment that removed whole `BinOutput/Quest`; not production-ready.

This inventory is a Git data/field comparison, **not** a bug list or a recommendation to restore historic conditions. Require a narrowly scoped reproduction, safe checks and CI before proposing a resource patch upstream.
