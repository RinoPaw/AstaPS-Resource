# Reverse-engineering intermediates

This directory keeps reproducible intermediate data used while recovering current Genshin protocol and IL2CPP information for AstaPS.

Raw game executables and `global-metadata.dat` samples are intentionally not committed. Keep them locally and identify them by cryptographic hashes. Commit only derived data, small reproducibility tools, observations, and evidence needed for another researcher to repeat the analysis.

## Layout

- `samples/<version>/<platform>/`: sample manifests, hashes, format fingerprints, and tool/version notes.
- `cmdids/<version>/`: protocol opcode observations and evidence state.
- `investigations/`: focused reverse-engineering notebooks for unresolved symbols/opcodes.
- `tools/`: small reproducibility utilities that do not depend on private local paths.
- Future generated artifacts such as filtered `script.json` slices, RVA tables, vtable maps, parser maps, and string-literal indexes should live under a version/platform-specific directory and record the input sample hashes that produced them.

## Evidence states

Use evidence labels consistently:

- `runtime-verified`: observed against the matching client and the semantic behavior is confirmed.
- `static-verified`: recovered from the matching client executable/metadata and cross-checked structurally.
- `observed-unresolved`: an opcode/value was observed, but its semantic name is still unknown.
- `mapped-not-observed`: present in a current mapping, but not observed in the runtime trace being discussed.
- `historical-only`: known from an older client; never treat it as a current-version mapping without fresh evidence.
- `hypothesis`: useful lead awaiting proof.

For protocol work, numeric equality from an older version is never sufficient evidence because Genshin CmdIds are routinely remapped between versions.

## Reproducing a sample fingerprint

```bash
python reverse/tools/fingerprint_metadata.py /path/to/global-metadata.dat \
  --game-version 7.1.0 --platform Windows
```

The output is JSON and should be committed as the sample manifest after checking that the version/platform labels match the source sample.

## Current focus

The first tracked sample is Genshin 7.1.0 Windows. Current protocol work follows the workflow documented in AstaPS at `docs/cmdid-recovery-from-client-logic.md`: use runtime observations to identify a concrete CmdId, recover the matching client packet class and `GetCmdId()` constant, then trace parser/vtable/call-site evidence before assigning a semantic name.
