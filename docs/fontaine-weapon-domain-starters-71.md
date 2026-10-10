# Fontaine weapon-domain starter-key compatibility (7.1)

The pinned 7.1 resource pack has a valid `scene40770.lua` through
`scene40773.lua`, each referencing a block that was absent from the pack.
Consequently, entering dungeon 4473 reported missing
`scene40773_block40773.lua`, no combat/reward groups, and no starter key.

These **synthetic compatibility** scripts provide the minimal block and groups
expected by AstaPS `MissingDomainFallbackManager` for scenes 40770–40773:
combat group `24077N001`, reward group `24077N004`, starter key config
`9001` (gadget 70360010, worktop option 7), and reward configs `5001` (gadget 70340012) and `5002` (gadget 70350008). Monster configs correspond to the Java fallback waves.
These scripts are **not native 7.1 group reconstructions**. Combat monsters,
their positions and levels are compatibility substitutes.

The server-side default challenge and reward logic remains authoritative.
A complete test must verify scene script loading, worktop interaction, both
combat waves, success settlement, the reward gadget, and resin deduction.
Run `python scripts/validate_fontaine_weapon_domains.py` for static checks.

Deploy only under `resources/Scripts/Scene/{40770..40773}` from this
resource branch alongside the AstaPS test build. Restart the server so its
Lua group/block metadata is reloaded.

## Visible challenge-key prefab

The first compatibility pass used gadget 70350096 at (0, 0.15, 4). Server logs
confirmed entity creation and option 7, but client users reported no visible key
or monsters. The known-working domain 40501 uses 70360010 at approximately
(0, 0, 0), so compatibility keys now use the same worktop prefab and location.
This is a targeted compatibility hypothesis pending client confirmation;
server-side presence alone is insufficient to prove client visibility.

## Reward fixture alignment (client follow-up)

In domain 4473, the scripted challenge completed, and server output showed
`dmFinished=true` and `exitLit=1`, but the player found no claim interaction
at the end of the room. The first compatibility draft put a lone reward tree
`70350008` at `(0, 0.15, -28)`. That is not the actual finish fixture used
in verified playable domain 5001 (scene 40501).

This revision reuses the **two-piece** 40501 reward arrangement with its
original heights and positions: `70340012` (config 5001) at
`(0.300, 0.100, -69.700)` and `70350008` (config 5002) at
`(0.412, 4.061, -65.517)`. These are **compatibility placements**, not
recovered native 4077x coordinates. The Java reward helper already activates
known exit gadgets on successful completion. The static resource check guards
both fixtures and their placement; client verification is still required.
