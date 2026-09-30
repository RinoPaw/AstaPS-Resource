#!/usr/bin/env python3
"""Emit a stable JSON fingerprint for an IL2CPP global-metadata.dat sample."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

STANDARD_IL2CPP_MAGIC = bytes.fromhex("af1bb1fa")
MHY_MAGIC = b"MHY\x00"


def digest(path: Path, name: str) -> str:
    h = hashlib.new(name)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(head: bytes) -> str:
    if head.startswith(MHY_MAGIC):
        return "mhy-obfuscated"
    if head.startswith(STANDARD_IL2CPP_MAGIC):
        return "standard-il2cpp"
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--game-version")
    parser.add_argument("--platform")
    args = parser.parse_args()

    with args.metadata.open("rb") as f:
        head = f.read(32)

    out = {
        "file_name": args.metadata.name,
        "size_bytes": args.metadata.stat().st_size,
        "format": classify(head),
        "magic_hex": head[:4].hex(),
        "header_32_hex": head.hex(),
        "sha256": digest(args.metadata, "sha256"),
        "sha1": digest(args.metadata, "sha1"),
        "md5": digest(args.metadata, "md5"),
    }
    if args.game_version:
        out["game_version"] = args.game_version
    if args.platform:
        out["platform"] = args.platform

    print(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
