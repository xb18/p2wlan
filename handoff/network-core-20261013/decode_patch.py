#!/usr/bin/env python3
"""Decode and verify the portable handoff patch without overwriting files."""
import base64
import hashlib
import json
import os
import sys
from pathlib import Path

EXPECTED_BYTES = 5930
EXPECTED_SHA256 = "c2bc69def2d3abcea3468bae0bcb466c7bff7b1ffad706f193cde0012ac62071"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 decode_patch.py OUTPUT.patch")
    source = Path(__file__).with_name("b19-runtime-handoff.patch.json")
    item = json.loads(source.read_text(encoding="utf-8"))
    if set(item) != {"encoding", "bytes", "sha256", "content"} or item["encoding"] != "base64":
        raise SystemExit("invalid patch envelope")
    raw = base64.b64decode(item["content"], validate=True)
    digest = hashlib.sha256(raw).hexdigest()
    if item["bytes"] != EXPECTED_BYTES or len(raw) != EXPECTED_BYTES:
        raise SystemExit("patch length mismatch")
    if item["sha256"] != EXPECTED_SHA256 or digest != EXPECTED_SHA256:
        raise SystemExit("patch checksum mismatch")
    output = Path(sys.argv[1])
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    print(f"PASS decoded patch: {len(raw)} bytes; SHA256 {digest}")

if __name__ == "__main__":
    main()
