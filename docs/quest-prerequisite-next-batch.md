# Quest prerequisite next batch

Updated: 2026-10-04

This note records the first evidence-backed prerequisite batch discovered after the completed Mondstadt Prologue I-III repair. It is intentionally a review/evidence note; the rows below have not yet been applied to the resource data.

## Scope

- Immediate post-Prologue hidden continuation: main quest `400`.
- Liyue Archon Quest Chapter I entry/main quest: `1000` (`Actor/Quest/MQ1000`, chapter `1101`, series `1101`).
- Historical references: `TomyJan/GCResource` branches `3700` and `4000`.

For `1000.json`, branches `3700` and `4000` resolve to the same Git blob:

```text
4cf32a438101a81501bb099d1e8ad2b5696990ee
```

That gives exact whole-file prerequisite consensus for the old `1000` graph, not merely row-by-row agreement.

## 40001

Current 7.1 source `BinOutput/Quest/400.json` has no meaningful `acceptCond` on `40001`.

Current flattened `ExcelBinOutput/QuestExcelConfigData.json` has:

```text
40001: STATE_EQUAL 0 FINISHED
```

Both 3.7 and 4.0 historical resources have:

```text
39604 FINISHED -> 40001
```

This is the established `zeroed-predecessor` conversion defect family. It is especially important because it sits directly after the repaired Prologue Act III graph.

## Main quest 1000

Current 7.1 `BinOutput/Quest/1000.json` has lost the meaningful subquest `acceptCond` graph. The flattened file retained a mostly order-linearized graph. Historical 3.7/4.0 data instead contains several fan-outs plus one state-value distinction.

Expected historical prerequisite graph:

```text
100099 <- 99902 FINISHED
100098 <- 99902 FINISHED
100000 <- 39604 FINISHED
100001 <- 100000 FINISHED

100002 <- 100001 FINISHED
100003 <- 100001 FINISHED
100004 <- 100001 FINISHED
100005 <- 100001 FINISHED
100006 <- 100001 FINISHED
100016 <- 100001 FINISHED

100007 <- 100006 FINISHED

100021 <- 100007 FINISHED
100022 <- 100007 FINISHED
100023 <- 100007 FINISHED
100024 <- 100007 FINISHED
100025 <- 100007 FINISHED

100026 <- 100024 FINISHED
100008  <- 100026 FINISHED
100015  <- 100008 FINISHED
100009  <- 100015 FINISHED
100027  <- 100009 FINISHED
100010  <- 100009 FINISHED

100011 <- 100010 state 4
100012 <- 100010 FINISHED
100013 <- 100012 FINISHED
100014 <- 100013 FINISHED
```

The flattened 7.1 rows that currently differ from that consensus are:

```text
100099: 0/FINISHED       -> 99902/FINISHED
100098: 100099/FINISHED  -> 99902/FINISHED
100000: 100098/FINISHED  -> 39604/FINISHED
100003: 100002/FINISHED  -> 100001/FINISHED
100004: 100003/FINISHED  -> 100001/FINISHED
100005: 100004/FINISHED  -> 100001/FINISHED
100006: 100005/FINISHED  -> 100001/FINISHED
100016: 100006/FINISHED  -> 100001/FINISHED
100022: 100021/FINISHED  -> 100007/FINISHED
100023: 100022/FINISHED  -> 100007/FINISHED
100024: 100023/FINISHED  -> 100007/FINISHED
100025: 100024/FINISHED  -> 100007/FINISHED
100026: 100025/FINISHED  -> 100024/FINISHED
100010: 100027/FINISHED  -> 100009/FINISHED
100011: 100010/state 3   -> 100010/state 4
100012: 100011/FINISHED  -> 100010/FINISHED
```

So main quest `1000` contributes 16 flattened differences.

Ten additional `1000` rows already have the historical predecessor in flattened QuestExcel, but their current 7.1 BinOutput source row has lost `acceptCond`. They should still be included in the evidence manifest so regeneration cannot destroy them again:

```text
100001
100002
100007
100021
100008
100015
100009
100027
100013
100014
```

## Planned repair batch

The next manifest batch should therefore contain:

- `40001`;
- all 26 subquests of main quest `1000`.

Expected effects when the existing strict fixers are run:

- source repair: restore 27 rows across `400.json` and `1000.json`;
- flattened repair: change 17 rows (1 in `400`, 16 in `1000`) and verify the other 10 `1000` rows as already correct;
- no server-side quest-ID workaround.

Before applying, keep the same safety rules used for the Prologue batch:

1. use exact normalized 3.7 + 4.0 consensus only;
2. preserve the `100011` state `4` prerequisite exactly;
3. restore fan-out edges instead of serializing by order;
4. patch BinOutput source and flattened QuestExcel together;
5. run both fixers in `--check` mode after application;
6. rerun the dual-reference audit focused on main quests `400` and `1000` and require zero remaining differences for the manifest-backed rows.
