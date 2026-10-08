# Mondstadt 7.1 quest compatibility on play/rino

Base: `play/rino` at `25fe7ad6`. Working branch:
`fix/mondstadt-prologue-rino-71`.

## Port policy

We compared all 40 Mondstadt prologue MainQuest JSON files with the
historical-evidence integration branch. Most Quest fields already matched.
Only **22 MainQuest files** required field-level compatibility changes.
All other fields and all unrelated resources stay exactly as they were
on play/rino; do not merge the older integration branch wholesale.

Reviewed changes cover:
- 35301: remove incorrect early trial Amber grant; 35402: grant Amber at
  the intended quest stage; restore tutorial and hilichurl spawn actions;
- 35901: preserve weather-area activation (area 3) and reset (areas 3, 1),
  without pretending the Java weather-gadget handler exists;
- 30710, 30810, 30814, 31101, 35901: OR alternatives;
  30901: AND requirement for dungeon IDs 1001, 1, 1003;
- 35203, 37602, 39703, 38802, 39404: reviewed OR failure routes;
- Acts II/III: reviewed item rewards, scene group starts, seal notifications,
  battle retries, teleport unlocking and dungeon-side actions.

Source categories must remain distinct: native 7.1 Quest fields,
historical compatibility, Lua group data, and server effects.

## Validation

`python tools/audit_mondstadt_prologue.py` checks the 40 MainQuests,
subquest handoffs, event/actions, Lua evidence and 35901 weather-area mapping.
`python -m unittest discover -s tools -p 'test_mondstadt_drift.py'`
checks drift classifications. Workflow
`.github/workflows/mondstadt-prologue-audit.yml` runs these checks
for the rino port branch. This static coverage does not demonstrate
real-client completion.

The paired server work is in
`RinoPaw/AstaPS:fix/mondstadt-runtime-rino-71`, preserving
`play/rino`'s NativeQuestOverlay and per-field provenance.
