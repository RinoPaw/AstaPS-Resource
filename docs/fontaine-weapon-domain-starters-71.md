# Fontaine weapon-domain starter-key compatibility (7.1)

The pinned 7.1 resource pack has a valid `scene40770.lua` through
`scene40773.lua`, each referencing a block that was absent from the pack.
Consequently, entering dungeon 4473 reported missing
`scene40773_block40773.lua`, no combat/reward groups, and no starter key.

These **synthetic compatibility** scripts provide the minimal block and groups
expected by AstaPS `MissingDomainFallbackManager` for scenes 40770–40773:
combat group `24077N001`, reward group `24077N004`, starter key config
`9001` (gadget 70350096, worktop option 7), and reward config `5001`
(gadget 70350008). Monster configs correspond to the Java fallback waves.
These scripts are **not native 7.1 group reconstructions**. Combat monsters,
their positions and levels are compatibility substitutes.

The server-side default challenge and reward logic remains authoritative.
A complete test must verify scene script loading, worktop interaction, both
combat waves, success settlement, the reward gadget, and resin deduction.
Run `python scripts/validate_fontaine_weapon_domains.py` for static checks.

Deploy only under `resources/Scripts/Scene/{40770..40773}` from this
resource branch alongside the AstaPS test build. Restart the server so its
Lua group/block metadata is reloaded.
