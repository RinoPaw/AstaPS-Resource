# Global 7.1 ley-line Lua group coverage

This is a **resource availability** audit using checked-in BlossomGroups and scene Lua files. It does **not** authenticate any sources against the original Global 7.1 EXE, metadata or assets. No missing coordinates or gadget definitions are inferred.

Run from the AstaPS-Resource checkout in PowerShell:

    python .\scripts\audit_blossom_lua_71.py --city 5 --rank 18
    python .\scripts\audit_blossom_lua_71.py --city 5 --rank 18 --json
    python -m unittest discover -s scripts -p test_audit_blossom_lua_71.py

## Source coverage at initial audit (AR 18; scene 3)

| City | Eligible camps | Lua groups present | Lua groups absent |
| --- | ---: | ---: | ---: |
| 1 | 31 | 28 | 3 |
| 2 | 15 | 15 | 0 |
| 3 | 22 | 22 | 0 |
| 4 | 45 | 36 | 9 |
| 5 (Fontaine) | 27 | 2 | 25 |
| 6 | 41 | 7 | 34 |
| 7 | 19 | 5 | 14 |
| 8 | 9 | 1 | 8 |

The only present Fontaine camp groups at this rank are camp 504014001 / group 133403311 and camp 504018001 / group 133412176. Both define blue gadget 70360057. There are no present Fontaine gold gadgets (70360056) among the 27 referenced groups. Group 133412176 is explicitly marked Auto-generated spawn data.

The native-source status of those coordinates is unknown. The report identifies gaps in the imported resource pack; recovering the original group scripts requires direct original-game evidence. Do not fill the missing 25 Fontaine scripts by copying or guessing locations.
