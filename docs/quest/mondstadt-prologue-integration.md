# Genshin 7.1 Mondstadt Prologue integration contract

Scope: birth/prelude plus Prologue Acts I, II and III through 39604; derived
from RinoPaw/Genshin-Reverse versioned Mondstadt mainline manifest. Quest 361 is
the WQ-typed transition for the 353 -> 355 forest segment, included only as a
support check. Hidden chapter controllers 363, 370 and 397 must not be
linearized with visible objectives.

## Ownership (do not substitute one source for another)

- **Client-native**: current 7.1 QuestExcel and full Quest fields recovered
  by Genshin-Reverse. Full Quest owns finishCond/failCond/finishExec/failExec;
  ordinary acceptCond/beginExec do not belong to the 7.1 full Quest payload.
- **Compatibility**: reviewed historical 3.7 and 4.0 Quest beginExec,
  corroborated by current 7.1 Lua group suites and their progress events.
  These are explicitly NOT recovered 7.1 native beginExec.
- **Asta materialization**: current QuestExcel flattened accept conditions
  may include previous-physical-row chains. These are not evidence of native
  7.1 prerequisites and must not override verified chapter logic.
- **Server runtime**: PR #71 and companion PR #87 / previously merged #84.
  Suite dispatch needs script initialization and group persistence, quest
  event delivery, real NPC/talk handling, object callbacks and scene effects.

## Reviewed compatibility restorations

| Subquest | Recovered semantic action | Evidence |
| --- | --- | --- |
| 35301 / 35302 | scene 3 group 133003002 suite 1 / 2 | original pre-c98b896710 resource; 7.1 Lua |
| 35402 | reward item 1021 | historical GCResource 3700/4000 |
| 35404 | notify scene 3 group 133003439 | GCResource; current Lua 35404 trigger |
| 36001 | scene 3 group 133003435 suite 1 | GCResource 3700+4000; current 7.1 Lua suite 1 monster 1442 / quest progress |
| 36003 | scene 3 group 133003136 suite 1 | GCResource 3700+4000; current 7.1 Lua suite 1 monsters 623,1443,1444 / quest progress |
| 35901 | SET_WEATHER_GADGET (3,1) on begin | GCResource 3700+4000, matching historical 359 progression |
| 30904 | ADD_QUEST_PROGRESS 359011 by 1 on begin | GCResource 3700+4000, supports 359 branch |
| 31101 / 35901 | finishCondComb LOGIC_OR | both historical versions; #13 also repairs |
| 35301 | no early GRANT_TRIAL_AVATAR | proven accidental addition c98b896710 |

All materialized actions remain source-scoped; no hardcoded quest-ID runtime
bypass. This table is a *minimum proved subset*, not proof that the remaining
Mondstadt quest graphs are correct or complete.

## Static checks and open integration risks

Run `python tools/audit_mondstadt_prologue.py` and
`python tools/verify_prologue_35301.py` with 7.1 Resource data. The audit
checks the whole scoped MainQuest population and exact actions above, plus
scene Lua linkage and spreadsheet override conflicts where present. Unknown
`acceptCond` and `beginExec` are not fabricated. This cannot exercise:

1. Real-time server event to quest completion / action execution.
2. Quest-owned monster lifetime across scene loading and group replacement.
3. Prologue Acts II/III mechanics (chest drops, elevators, seal battles,
   Dungeon scene re-entry, Stormterror combat); these need specific PR #13/#87
   review and matching runtime support before a full-client-test claim.
4. Existing saved accounts stuck in older task state.

Do not request a client test before the full CI gates are green. Existing
generic prerequisite audit failures outside this scope must be reported
separately; they are not evidence this new scoped check passed.

## Imported evidence-supported companion work

Select native-resource-side changes from upstream resource PR #13 are folded
in without copying QuestExcel wholesale: Act II 20101 route 3; Act III
Stormterror group keepalive and name IDs; Light Guiding Ceremony seal
ability/Lua state handling. Companion server runtime is drawn from PR #87
and PR #71 with chapter bootstrap-at-birth explicitly excluded.

**Not yet imported:** PR #13's broad flattened QuestExcel changes (several
hundred entries), because the native 7.1 Quest ownership boundary requires
per-condition provenance and avoids silently replacing the entire table.
Remaining acceptance graph and cross-scene visual gameplay must be checked
after code and CI validation. Do not claim three-act completion based only
on static resources.

## Drift reporting semantics

Historical STATE_EQUAL/STATE_NOT_EQUAL arrays often carry a third zero padding
value; the scoped report normalizes that layout. Missing BinOutput compatibility
is counted separately, not treated as a proven Excel defect. Predecessor,
combinator and Quest-0 placeholder conflicts remain visible but are evidence
candidates, never automatically overwritten or promoted to 7.1 native data.

## Act I elemental tutorial sequence

The static gate now verifies the first fire slime (35302/439) and the later
quest-triggered slime waves: 35303 -> group 133003448 -> monsters 440,441;
35304 -> group 133003449 -> monsters 442..445. Both Lua groups must send
progress 1330030023/4, chained through 35310/35311. The 35304 burst-energy
action is required. These links are native 7.1 Lua evidence corroborating
the retained compatibility beginExec; they do not prove in-game visibility.

## Further reviewed Act II / Act III compatibility

Historical GCResource 3.7 and 4.0 agree on the restored actions. The
current 7.1 Lua files confirm the referenced group suites, monster configs
and quest-start notification sources:

- 37303, 38202, 39703: start the scene groups required by objectives.
- 2010101: consume hideout key and enable gadget; 2010102: trial 11,
  matched by its existing removal at 2010151; seven key-reward branches.
- 37203, 38303, 38406: story items 100164, 100163, 100165.
- 38402: rollback on fail; 38905 / 39003: Lua group 133007227.
- 39401: unlock point 3/38 for dungeon approach.
- 39801, 39808, 39812, 39604: closing-act gadget suites and Lua link.

We intentionally did not import historical 37903 gainItems(1021):
permanent Amber is already restored in 35402 and a second grant requires
7.1-specific evidence. None of the compatibility restorations claims to
be a native 7.1 beginExec/acceptCond field.
