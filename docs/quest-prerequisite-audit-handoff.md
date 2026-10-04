# Quest prerequisite audit handoff

Updated: 2026-10-04

This document records the current state of the AstaPS 7.1 quest prerequisite/resource audit so another session can continue without reconstructing the investigation.

## Repositories / heads

- Server: `RinoPaw/AstaPS`, branch `play/rino`
  - Known head at handoff: `2d8ffe7f` (`revert: keep chapter starts resource-driven [skip ci]`)
  - The server-side experiment that treated `[0,3]` as a generic chapter-root sentinel was reverted. Chapter starts remain resource-driven.
- Resource: `RinoPaw/AstaPS-Resource`, branch `main`
  - Handoff doc commit is newer than `47693259`.
  - `47693259` = `tools: require multi-version quest audit consensus [skip ci]`

## Root cause established so far

The 7.1 resource conversion is not only losing isolated quest IDs. It frequently damages the quest prerequisite graph while flattening `BinOutput/Quest` into `ExcelBinOutput/QuestExcelConfigData.json`.

Observed defect families:

1. Real predecessor becomes `QUEST_COND_STATE_EQUAL [0,3]`.
2. A parallel/fan-out graph is incorrectly serialized into a linear `previous order -> next order` chain.
3. Compound accept conditions are reduced to one condition.
4. `acceptCondComb` is lost or changes (AND/OR drift).
5. State values drift (`UNFINISHED`, `FINISHED`, `FAILED`, etc.).
6. Some 7.x BinOutput source rows genuinely have no `acceptCond`; the flattened `[0,3]` in those rows must not automatically be treated as corruption.

Do not globally reinterpret `[0,3]` in server code.

## Banner investigation / chapter 1001

The missing "The Outlander Who Caught the Wind" chapter banner was traced to hidden chapter controller quest `36301`.

Correct historical prerequisite:

```text
35202 FINISHED
    -> 36301 START
    -> GameQuest.start()
    -> ChapterStateNotify(chapterId=1001, BEGIN)
    -> client chapter banner
```

Current broken 7.1 flattening had `36301 acceptCond = [0,3]`.

Server `PacketChapterStateNotify` matches LunaGC 7.1 and does not need an ID-specific fix.

Resource repair was added instead:

- `69ba8692 fix: restore chapter 1001 controller prerequisite [skip ci]`
- `751e36c0 tools: repair chapter 1001 controller prerequisite [skip ci]`

The earlier server-side generic chapter-root workaround was reverted and must stay reverted.

## Skip-intro investigation already completed

Separate previous issue: skipping new-account intro caused 35104 replay + Paimon moving early.

Root cause was lifecycle/timing, not 35100's condition:

- skip path called fresh-player quest bootstrap before scene-ready handshake;
- it also resent a full quest snapshot after `onPlayerBorn()`, reloading the freshly-created quest actor.

`play/rino` was regularized so automatic birth skips visible selection/native intro while preserving normal world/scene lifecycle:

```text
auto birth
-> player login/world entry
-> EnterSceneReady / SceneInit / EnterSceneDone
-> PostEnterSceneRsp
-> onPlayerBorn()
-> 35104
```

Keep this engineering rule: skipping presentation must not skip protocol/lifecycle boundaries.

## Current audit tools

### `tools/audit_zero_state_equal.py`

Audits flattened `QUEST_COND_STATE_EQUAL [0,3]` and distinguishes:

- `historical-repair`: an intact historical reference has a non-zero predecessor;
- `source-root-or-external`: the current 7.x `BinOutput/Quest` source row itself has no meaningful accept condition, so no predecessor may be invented.

The current 7.1 run supplied by the user produced:

```text
candidate_count: 3771
historical-repair: 929
source-root-or-external: 2842
```

Examples of legitimate source-root/external candidates confirmed in current 7.x BinOutput:

- `7710201`
- `7716203`
- `7722201`

Their source BinOutput rows have no meaningful `acceptCond`; do not repair them merely because flattened Excel contains `[0,3]`.

### `tools/audit_quest_prerequisite_drift.py`

Full prerequisite-graph comparison tool. It reports:

- `zeroed-predecessor`
- `predecessor-drift`
- `conditions-lost`
- `conditions-added`
- `combiner-drift`
- `condition-drift`
- `reference-disagreement`

As of `47693259`, `--reference-bin-root` is repeatable. Multiple historical versions must agree on normalized `acceptCond + acceptCondComb`; disagreement is reported and is not treated as evidence for repair.

Recommended reference pair for old Mondstadt content:

```text
TomyJan/GCResource branch 3700
TomyJan/GCResource branch 4000
```

## User's full 3.7-reference audit results

The uploaded full drift report contained:

```text
zeroed-predecessor: 2692
predecessor-drift: 2465
match: 4927
condition-drift: 5141
conditions-lost: 1785
combiner-drift: 43
conditions-added: 262
reference_missing: 7946
```

This is intentionally NOT a repair count. Many rows changed legitimately between 3.7 and 7.1, and many 7.1 quests did not exist in 3.7.

For the known Mondstadt Prologue I-III main-quest set, the same report yielded 142 differences:

```text
predecessor-drift: 86
zeroed-predecessor: 44
conditions-lost: 7
condition-drift: 4
conditions-added: 1
```

The current evidence manifest covers 47 of those currently-different rows. Residual Prologue differences: 95.

Residual distribution:

```text
predecessor-drift: 81
conditions-lost: 6
zeroed-predecessor: 4
condition-drift: 3
conditions-added: 1
```

Do NOT import those 95 from 3.7 blindly. Cross-check them against 4.0 first using the new multi-reference consensus mode.

## Repairs already in the evidence manifest

The existing `tools/fix_quest_prerequisites.py` manifest contains evidence-backed repairs for early/new-player and Mondstadt Prologue entries, including:

- 351/352 early handoff;
- Act I cross-main entries and non-linear controllers;
- `36301 <- 35202` chapter 1001 controller;
- Act II cross-main chain through the temple branches;
- compound `38301` requiring `38004 + 38105 + 38202` with `LOGIC_AND`;
- Act III cross-main handoffs through 397/388/389/390/393/394/398/396/399.

Relevant commits include:

- `c0d1032f` evidence-backed early/Act-I expansion
- `b77e8f8d tools: restore Prologue Act II quest handoffs [skip ci]`
- `9de046d7 tools: restore Prologue Act III quest handoffs [skip ci]`
- `0555a865 tools: repair BinOutput quest prerequisites from evidence manifest [skip ci]`
- `ec9f8e70 tools: audit quest prerequisite drift [skip ci]`
- `7ab4234c tools: distinguish source-root zero prerequisites [skip ci]`
- `47693259 tools: require multi-version quest audit consensus [skip ci]`

`fix_binoutput_quest_prerequisites.py` uses the same evidence manifest to restore source `BinOutput/Quest` rows, preventing regeneration from immediately losing the repaired prerequisites again.

## Next-session first task

Run a dual-reference audit against both 3.7 and 4.0, then isolate the 95 residual Mondstadt Prologue differences that have 3.7/4.0 consensus.

Suggested local setup (from the AstaPS-Resource repo):

```powershell
$root = Split-Path (Resolve-Path .).Path -Parent
$ref3700 = Join-Path $root "GCResource-3700"
$ref4000 = Join-Path $root "GCResource-4000"

if (-not (Test-Path $ref3700)) {
    git clone --depth 1 --filter=blob:none --sparse --branch 3700 https://github.com/TomyJan/GCResource.git $ref3700
    git -C $ref3700 sparse-checkout set BinOutput/Quest
}

if (-not (Test-Path $ref4000)) {
    git clone --depth 1 --filter=blob:none --sparse --branch 4000 https://github.com/TomyJan/GCResource.git $ref4000
    git -C $ref4000 sparse-checkout set BinOutput/Quest
}

python .\tools\audit_quest_prerequisite_drift.py `
    .\ExcelBinOutput\QuestExcelConfigData.json `
    --reference-bin-root "$ref3700\BinOutput\Quest" `
    --reference-bin-root "$ref4000\BinOutput\Quest" `
    --only-differences `
    --json .\audit-prerequisite-consensus-3700-4000.json `
    > .\audit-prerequisite-consensus-3700-4000.txt
```

The output is redirected to files on purpose; the previous terminal output was too large and got truncated.

After that:

1. Filter to the Prologue main IDs listed below.
2. Exclude existing manifest subIds.
3. Keep only rows with `reference_consensus_count == 2` and no `reference-disagreement`.
4. Inspect compound conditions carefully; do not auto-generate `Repair(one(...))` for multi-condition rows.
5. Add evidence-backed rows to `REPAIRS` in coherent batches, with `[skip ci]` commits.
6. Run both `fix_quest_prerequisites.py --check` and `fix_binoutput_quest_prerequisites.py --check` after applying source repairs.

Known Prologue main IDs used for the 142/95 statistics:

```text
306 307 308 309 311
351 352 353 354 355 356 357 358 359 360 361 362 363
370 371 372 373 374 375 376 377 20101 379 380 381 382 383 384
397 388 389 390 393 394 398 396 399
```

## Safety / methodology rules

- Never treat every `[0,3]` as corruption.
- Never add a server-side quest-ID workaround when resource evidence exists.
- Prefer intact historical BinOutput evidence; for old content, require 3.7 + 4.0 consensus before broad batch repair.
- A later-version historical mismatch can be a legitimate quest redesign; classify it as `reference-disagreement`, do not guess.
- Restore source `BinOutput/Quest` as well as flattened QuestExcel for confirmed extraction defects.
- Keep repair scripts idempotent and strict: unexpected current shapes should fail rather than silently overwrite.
- Do not let CI slow this audit; commits use `[skip ci]`.
