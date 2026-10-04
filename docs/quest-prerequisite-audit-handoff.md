# Quest prerequisite audit handoff

Updated: 2026-10-04

This document records the current state of the AstaPS 7.1 quest prerequisite/resource audit so another session can continue without reconstructing the investigation.

## Repositories / branches

- Server: `RinoPaw/AstaPS`, branch `play/rino`
  - The server-side experiment that treated `[0,3]` as a generic chapter-root sentinel was reverted.
  - Chapter starts remain resource-driven.
- Resource: `RinoPaw/AstaPS-Resource`, branch `main`.
- Historical references: `TomyJan/GCResource`, branches `3700` and `4000`.

## Current status: audited and repaired through Chapter 1207

The prerequisite repair now covers the Mondstadt Prologue, Liyue old-content chapters, Inazuma chapters through 1204, Liyue Interlude Chapter 1205, Chapter 1206, and Chapter 1207.

Permanent CI is `.github/workflows/quest-prerequisite-audit.yml`.

Current permanent validation covers:

```text
regular strict Repair manifest: 678 unique subquests
Chapter 1104 missing-row special restore: 42 subquests
Chapter 1206 missing-row special restore: 53 subquests
```

All three checks are clean and idempotent at the latest Chapter 1207 permanent-audit run.

Important recent resource commits:

```text
a482fe0e  fix: restore Chapter 1205 prerequisites [skip ci]
f0734bc3  fix: restore Chapter 1206 quest rows and prerequisites [skip ci]
893952b4  fix: restore Chapter 1207 prerequisites [skip ci]
7e82f211  ci: require Chapter 1207 prerequisite idempotence
```

Temporary discovery/apply workflows are removed after each chapter is validated and absorbed into the permanent audit.

## Root cause established

The 7.1 resource conversion damages the quest prerequisite graph while flattening `BinOutput/Quest` into `ExcelBinOutput/QuestExcelConfigData.json`.

Observed defect families:

1. Real predecessor becomes `QUEST_COND_STATE_EQUAL [0,3]`.
2. A parallel/fan-out graph is serialized as an incorrect linear previous-order -> next-order chain.
3. Compound accept conditions are reduced to one condition.
4. `acceptCondComb` is lost or changes, including nontrivial historical combiners.
5. State values drift, including historical state 4 becoming state 3.
6. Some 7.x BinOutput rows genuinely have no `acceptCond`; flattened `[0,3]` must not automatically be treated as corruption.
7. Some chapters retain source `BinOutput/Quest` rows but lose the corresponding flattened QuestExcel rows entirely.

Never globally reinterpret `[0,3]` in server code.

## Evidence threshold

For old content, the repair threshold is exact consensus between GCResource 3.7 and 4.0 on each subquest's normalized prerequisite semantics:

```text
normalized acceptCond + effective acceptCondComb
```

Whole-file byte identity is useful evidence but is not required.

Chapter 1207 established this boundary clearly: `1028.json` differs as a whole between 3.7 and 4.0, while every Chapter 1207 prerequisite row still has exact two-reference consensus. Unrelated field drift must therefore not block a prerequisite repair when the prerequisite semantics themselves agree.

If the two references disagree on prerequisite semantics or one reference lacks the row, classify it as disagreement/partial coverage and do not guess.

## Mondstadt Prologue completion

The known Prologue I-III set originally contained 142 prerequisite differences against the old graph:

```text
predecessor-drift: 86
zeroed-predecessor: 44
conditions-lost: 7
condition-drift: 4
conditions-added: 1
```

The first evidence manifest covered 47 rows. The remaining 95 all had exact GCResource 3.7 + 4.0 prerequisite consensus with no disagreement or partial coverage.

After restoring source and flattened resources, the Prologue dual-reference difference count became zero.

Important examples:

- `36301`: `35202 FINISHED -> 36301 START -> ChapterStateNotify(1001, BEGIN)`; this restores the Chapter 1001 banner without a server quest-ID workaround.
- `35104`: historical 3.7 and 4.0 both have no `acceptCond`; broken flattened 7.1 contained `[0,3]`. Correct repair is empty `acceptCond`.
- `35102`: three conditions with `LOGIC_OR`.
- `35103`: mixed EQUAL / NOT_EQUAL conditions with `LOGIC_AND`.
- `36203`: EQUAL + duplicate NOT_EQUAL conditions with `LOGIC_AND`.
- `37115`: EQUAL + NOT_EQUAL with `LOGIC_AND`.
- `38301`: `38004 + 38105 + 38202` with `LOGIC_AND`.
- Historical state 4 is preserved where evidenced, including `37504`, `37603`, and `38805`.

## Missing flattened-row chapters

### Chapter 1104

`BinOutput/Quest/8000..8003.json` retained all 42 subquests, but current 7.1 had lost their meaningful `acceptCond` and QuestExcel had zero flattened rows for the chapter.

`tools/fix_chapter1104_quest_rows.py`:

- restores prerequisite semantics from exact historical consensus;
- materializes flattened rows from the CURRENT 7.1 source rows;
- therefore preserves current descriptions, finish/fail conditions, exec data, guides, and other current-version fields;
- accepts only an all-42-missing or all-42-present state and refuses partial insertion.

### Chapter 1206

Chapter chain:

```text
8004 -> 8005 -> 8006 -> 8007
ChapterExcel range: 800402 -> 800710
```

All 53 historical prerequisite rows have exact 3.7 + 4.0 consensus. Current 7.1 source retained all 53 rows but lost every meaningful `acceptCond`; QuestExcel was missing all 53 rows.

`tools/fix_chapter1206_quest_rows.py` uses the same current-source materialization strategy as Chapter 1104 and refuses partial insertion states.

Resource commit: `f0734bc3`.

## Chapter 1207

Chapter chain:

```text
1019 -> 1028 -> 1029 -> 1030 -> 1031
ChapterExcel range: 101903 -> 103106
```

Historical evidence:

```text
subquests with exact 3.7 + 4.0 prerequisite consensus: 88
reference disagreements: 0
partial reference coverage: 0
```

Current 7.1 source:

```text
88/88 source rows present
88/88 meaningful acceptCond missing
```

Current flattened QuestExcel before repair:

```text
already correct: 38
prerequisite drift: 50
  predecessor-drift: 35
  zeroed-predecessor: 9
  conditions-lost: 5
  condition-drift: 1
```

Historical effective combiners across the 88 rows:

```text
LOGIC_AND: 85
LOGIC_A_AND_ETCOR: 2
LOGIC_A_OR_B_OR_ETCAND: 1
```

Important special rows:

- `101907`: eight-condition gate with `LOGIC_A_OR_B_OR_ETCAND`.
- `102901`: activity/state compound gate with `LOGIC_A_AND_ETCOR`.
- `103001`: activity/state compound gate with `LOGIC_A_AND_ETCOR`.
- `102912`: three STATE_EQUAL conditions with `LOGIC_AND`.
- `103010`, `103015`, `103004`: STATE_EQUAL + QUEST_VAR_EQUAL compound gates.
- `102936`: historical state is 4; broken flattened row used state 3.

`tools/fix_chapter1207_prerequisites.py` is a static strict manifest generated from the dual-reference consensus and the observed 7.1 damaged shapes. Direct invocation is scoped to Chapter 1207, while importing the module extends the cumulative regular manifest.

Resource + static manifest commit: `893952b4`.

Post-repair audit: 88/88 matches against the two historical references.

## Current tools

### `tools/fix_quest_prerequisites.py`

Core `Repair` model and flattened-row patcher.

`Repair` records:

```text
json_file
main_id
sub_id
desc_hash
expected_accept
damaged_accept
expected_comb
damaged_comb
```

Properties:

- idempotent;
- refuses unexpected current prerequisite shapes;
- preserves compound condition multiplicity;
- preserves exact known combiners;
- can whitelist a known damaged combiner only for the specific Repair row.

### `tools/fix_liyue_prerequisites.py`

Shared regular-manifest source + QuestExcel repair engine.

Source repair permits the known extraction-loss shape of missing `acceptCond`, but still refuses an unexpected nonempty prerequisite graph.

### `tools/fix_chapter1104_quest_rows.py`

Special current-source row materializer for the 42 missing Chapter 1104 flattened rows.

### `tools/fix_chapter1206_quest_rows.py`

Special current-source row materializer for the 53 missing Chapter 1206 flattened rows.

### `tools/fix_chapter1207_prerequisites.py`

Chapter 1207 strict static manifest, 88 rows.

### `tools/audit_quest_prerequisite_drift.py`

Reports classifications including:

- `zeroed-predecessor`
- `predecessor-drift`
- `conditions-lost`
- `conditions-added`
- `combiner-drift`
- `condition-drift`
- `current-missing-row`
- `reference-disagreement`

`--reference-bin-root` is repeatable. Multiple references must agree on normalized prerequisite semantics before the row is accepted as consensus evidence.

### `tools/filter_quest_prerequisite_consensus.py`

Filters the audit to complete N-reference consensus candidates and separates simple state-equal rows from manual/compound rows.

### `tools/audit_zero_state_equal.py`

Previous 7.1 global run:

```text
candidate_count: 3771
historical-repair: 929
source-root-or-external: 2842
```

Confirmed legitimate source-root/external examples include `7710201`, `7716203`, and `7722201`.

## Permanent CI

`.github/workflows/quest-prerequisite-audit.yml` currently validates:

1. the 678 unique regular `Repair` rows through Chapter 1207;
2. source BinOutput idempotence for the cumulative regular manifest;
3. flattened QuestExcel idempotence for the cumulative regular manifest;
4. Chapter 1104's 42 materialized rows;
5. Chapter 1206's 53 materialized rows.

Before asking for game testing or before a real upstream submission, do not skip the relevant CI/build validation.

## Skip-intro investigation already completed

Separate previous issue: skipping new-account intro caused 35104 replay + Paimon moving early.

Root cause was lifecycle/timing: the skip path bootstrapped fresh-player quests before the scene-ready handshake and resent a full quest snapshot after `onPlayerBorn()`.

`play/rino` preserves the normal lifecycle:

```text
auto birth
-> player login/world entry
-> EnterSceneReady / SceneInit / EnterSceneDone
-> PostEnterSceneRsp
-> onPlayerBorn()
-> 35104
```

Skipping presentation must preserve protocol/lifecycle boundaries.

## Next task: Chapter 1301

The next chronological Archon chapter in current `ChapterExcelConfigData.json` is Chapter 1301 (Sumeru):

```text
beginQuestId: 300002
endQuestId:   300612
terminal MQ:  3006
cityId:       4
needPlayerLevel: 35
```

Continue as follows:

1. Resolve the exact historical MQ chain beginning from MQ3000 by following `suggestTrackMainQuestList` until MQ3006. Do not infer the chain from filenames.
2. Run a 3.7 + 4.0 row-level prerequisite consensus audit for the complete chain.
3. Whole-file version differences are allowed; prerequisite-semantic disagreement is not.
4. Audit current 7.1 source membership and source `acceptCond` loss.
5. Determine whether current QuestExcel rows are present, damaged, or missing entirely.
6. Generate a strict static repair manifest from only exact dual-reference consensus rows, capturing the observed 7.1 damaged shapes as whitelists.
7. Simulate/apply, require `git diff --check`, exact modified-path allowlisting, and post-repair dual-reference zero-difference validation before committing.
8. Extend permanent CI, confirm green, then remove temporary discovery/apply workflows.

The Chapter 1207 generation approach is preferred for large future batches because it removes manual transcription risk while still committing a reviewable static manifest.

## Safety / methodology rules

- Never treat every `[0,3]` as corruption.
- Never add a server-side quest-ID workaround when resource evidence exists.
- Prefer intact historical BinOutput prerequisite evidence; require 3.7 + 4.0 row-level consensus for old content.
- A reference prerequisite mismatch may reflect a legitimate redesign; do not guess.
- Restore source `BinOutput/Quest` as well as flattened QuestExcel for confirmed extraction defects.
- If QuestExcel rows are absent, materialize them from current-version BinOutput and inject only evidence-backed prerequisite semantics.
- Keep repair scripts idempotent and strict. Unexpected current shapes must fail rather than be silently overwritten.
- Preserve exact compound-condition multiplicity and exact historical combiner values.
- Use temporary CI only for discovery/apply gates, then fold the result into permanent audit and remove temporary workflows.
