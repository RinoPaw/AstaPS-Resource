# AstaPS Resource — play/rino archive

This branch preserves historical 7.1 resource experiments. It is **not** the current deployment baseline. Use [AstaPS-Resource main](https://github.com/MeChen618/AstaPS-Resource/tree/main) for the latest upstream resources.

AstaPS expects resource data under its `resources/` directory, including `BinOutput/`, `ExcelBinOutput/`, `ScriptSceneData/` and `Server/`.

Reverse-engineering research and evidence belong in [Genshin-Reverse](https://github.com/RinoPaw/Genshin-Reverse). The older extracted 7.1 full Quest bundle is [preserved at a pinned Genshin-Reverse revision](https://github.com/RinoPaw/Genshin-Reverse/blob/6030649779ed0155dc289dd83c61fae1a2ca437a/versions/7.1.0-global/quests.json), rather than duplicated by this branch.

For the Chapter 1301 historical prerequisite audit and its unresolved 7.1-only row, see the [versioned research record](https://github.com/RinoPaw/Genshin-Reverse/tree/main/versions/7.1.0-global/analyses/quest-prerequisites/chapter1301). Earlier handoff documents and short-lived discovery workflows remain available in Git history at [`891ec4c`](https://github.com/RinoPaw/AstaPS-Resource/tree/891ec4c0377bca1854d879cf124a52b3967e1776).

Do not replay the obsolete QuestExcel overlay from this branch: it can reintroduce the premature 35301 Amber trial-avatar grant already fixed upstream.

The historical `tools/` repair scripts were removed from this archive branch after all 20 files were checked as byte-identical to the scripts in [upstream `main`](https://github.com/MeChen618/AstaPS-Resource/tree/5ff5f0b083fd3683aca894e4ebc2ba602306820f/tools). Earlier versions are still accessible through this branch's Git history. Do not run historical generators against modern production resources.
