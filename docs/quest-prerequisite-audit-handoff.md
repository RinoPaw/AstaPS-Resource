# Quest prerequisite audit handoff

Updated: 2026-10-04

This document records the current state of the AstaPS 7.1 quest prerequisite/resource audit so another session can continue without reconstructing the investigation.

## Repositories / heads

- Server: `RinoPaw/AstaPS`, branch `play/rino`
  - Known head at handoff: `2d8ffe7f` (`revert: keep chapter starts resource-driven [skip ci]`).
  - The server-side experiment that treated `[0,3]` as a generic chapter-root sentinel was reverted. Chapter starts remain resource-driven.
- Resource: `RinoPaw/AstaPS-Resource`, branch `main`
  - `a97c4337` = `tools: restore consensus Prologue prerequisite graph [skip ci]`
  - `b267bca7` = `fix: restore Prologue prerequisite graph [skip ci]`
  - The Mondstadt Prologue I-III prerequisite repair is now applied to both source `BinOutput/Quest` and flattened `ExcelBinOutput/QuestExcelConfigData.json`.

## Current status: Prologue audit completed

The known Mondstadt Prologue I-III set originally contained 142 prerequisite differences against the 3.7 reference:

```text
predecessor-drift: 86
zeroed-predecessor: 44
conditions-lost: 7
condition-drift: 4
conditions-added: 1
```

The first evidence manifest covered 47 rows. The remaining 95 rows were audited against both GCResource 3.7 and 4.0.

Residual distribution before repair:

```text
predecessor-drift: 81
conditions-lost: 6
zeroed-predecessor: 4
condition-drift: 3
conditions-added: 1
```

Dual-reference result for all 95 residual rows:

```text
reference_consensus_count: 2 for every row
reference_disagreements: 0
partial_reference_coverage: 0
```

The 95 consensus repairs were added to `tools/fix_quest_prerequisites.py` in `a97c4337` and then applied to the resources in `b267bca7`.

Post-repair validation:

```text
fix_binoutput_quest_prerequisites.py --check
    -> All evidence-backed BinOutput quest prerequisites are already restored.

fix_quest_prerequisites.py --check
    -> All evidence-backed quest prerequisite repairs are already applied.

3.7 + 4.0 dual-reference audit, Prologue I-III
    -> PASS: Prologue prerequisite differences = 0
```

The resource commit touched 39 tracked files: 38 `BinOutput/Quest/*.json` files plus `ExcelBinOutput/QuestExcelConfigData.json`.

## Root cause established

The 7.1 resource conversion damages the quest prerequisite graph while flattening `BinOutput/Quest` into `ExcelBinOutput/QuestExcelConfigData.json`.

Observed defect families:

1. Real predecessor becomes `QUEST_COND_STATE_EQUAL [0,3]`.
2. A parallel/fan-out graph is serialized as an incorrect linear previous-order -> next-order chain.
3. Compound accept conditions are reduced to one condition.
4. `acceptCondComb` is lost or changes between AND/OR.
5. State values drift, including rows where historical state 4 became state 3.
6. Some 7.x BinOutput rows genuinely have no `acceptCond`; flattened `[0,3]` must not automatically be treated as corruption.

Never globally reinterpret `[0,3]` in server code.

## Important repaired examples

### Chapter 1001 controller

The missing "The Outlander Who Caught the Wind" chapter banner was traced to hidden controller quest `36301`.

Correct flow:

```text
35202 FINISHED
    -> 36301 START
    -> GameQuest.start()
    -> ChapterStateNotify(chapterId=1001, BEGIN)
    -> client chapter banner
```

The server `PacketChapterStateNotify` matches LunaGC 7.1. The fix belongs in resources; no quest-ID server workaround is needed.

### 35104 source-root behavior

Historical 3.7 and 4.0 both have no `acceptCond` for `35104`, while the broken flattened 7.1 row contained `[0,3]`.

The correct repair is therefore an empty `acceptCond`, not an invented predecessor. This is an important example of why `[0,3]` cannot be treated globally as corruption with a non-zero historical predecessor.

### Compound / combiner repairs

The completed manifest preserves compound semantics rather than reducing them to a single predecessor. Examples include:

- `35102`: three conditions with `LOGIC_OR`
- `35103`: mixed EQUAL / NOT_EQUAL conditions with `LOGIC_AND`
- `36203`: EQUAL + duplicate NOT_EQUAL conditions with `LOGIC_AND`
- `37115`: EQUAL + NOT_EQUAL with `LOGIC_AND`
- `38301`: `38004 + 38105 + 38202` with `LOGIC_AND`
- `2010113`, `2010123`, `2010133`: two-condition `LOGIC_OR` branches

State-drift repairs include historical state 4 for `37504`, `37603`, and `38805`.

## Skip-intro investigation already completed

Separate previous issue: skipping new-account intro caused 35104 replay + Paimon moving early.

Root cause was lifecycle/timing:

- skip path called fresh-player quest bootstrap before scene-ready handshake;
- it also resent a full quest snapshot after `onPlayerBorn()`, reloading the freshly-created quest actor.

`play/rino` preserves normal lifecycle:

```text
auto birth
-> player login/world entry
-> EnterSceneReady / SceneInit / EnterSceneDone
-> PostEnterSceneRsp
-> onPlayerBorn()
-> 35104
```

Keep this rule: skipping presentation must preserve protocol/lifecycle boundaries.

## Current tools

### `tools/fix_quest_prerequisites.py`

Single strict evidence manifest for flattened `QuestExcelConfigData.json`.

Properties:

- idempotent;
- refuses unexpected current shapes;
- preserves compound conditions and `acceptCondComb`;
- allows negative `desc_hash` only where `json_file + main_id + sub_id` is intentionally the identity key.

### `tools/fix_binoutput_quest_prerequisites.py`

Uses the same manifest to repair source `BinOutput/Quest`, so regeneration cannot immediately recreate the flattened prerequisite damage.

### `tools/audit_quest_prerequisite_drift.py`

Reports:

- `zeroed-predecessor`
- `predecessor-drift`
- `conditions-lost`
- `conditions-added`
- `combiner-drift`
- `condition-drift`
- `reference-disagreement`

`--reference-bin-root` is repeatable. Multiple references must agree on normalized `acceptCond + acceptCondComb` before a row is considered consensus evidence.

Recommended old-content pair:

```text
TomyJan/GCResource branch 3700
TomyJan/GCResource branch 4000
```

### `tools/audit_zero_state_equal.py`

Previous 7.1 run:

```text
candidate_count: 3771
historical-repair: 929
source-root-or-external: 2842
```

Confirmed legitimate source-root/external examples include `7710201`, `7716203`, and `7722201`.

## Next task

The Mondstadt Prologue I-III set is complete. Do not re-audit or re-import those 142 rows unless resource inputs change.

The next useful expansion is to triage old-content prerequisite damage outside the Prologue using the same evidence threshold:

1. Start from rows present in current 7.1 plus both 3.7 and 4.0 references.
2. Require exact 3.7 + 4.0 consensus on normalized `acceptCond + acceptCondComb`.
3. Exclude rows already present in `REPAIRS`.
4. Separate simple single-predecessor rows from compound / state / combiner drift.
5. Check the current 7.1 source `BinOutput/Quest` before adding each repair batch.
6. Repair both source BinOutput and flattened QuestExcel.
7. Run both strict `--check` commands and a post-repair dual-reference audit before committing.

Do not attempt to turn the old full-audit difference counts into a global repair set. Many rows changed legitimately across versions or do not exist in both references.

## Known Prologue main IDs now complete

```text
306 307 308 309 311
351 352 353 354 355 356 357 358 359 360 361 362 363
370 371 372 373 374 375 376 377 20101 379 380 381 382 383 384
397 388 389 390 393 394 398 396 399
```

## Safety / methodology rules

- Never treat every `[0,3]` as corruption.
- Never add a server-side quest-ID workaround when resource evidence exists.
- Prefer intact historical BinOutput evidence; for old content, require 3.7 + 4.0 consensus before broad repair.
- A reference mismatch may reflect a legitimate redesign; classify it as `reference-disagreement` and do not guess.
- Restore source `BinOutput/Quest` as well as flattened QuestExcel for confirmed extraction defects.
- Keep repair scripts idempotent and strict. Unexpected current shapes must fail rather than be silently overwritten.
- Preserve exact compound-condition multiplicity when the historical references contain duplicates.
- Keep CI out of the critical path; audit and maintenance commits use `[skip ci]`.
