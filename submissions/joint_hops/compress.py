#!/usr/bin/env python3
"""Rebuild joint_hops' archive.zip from its stored sections and check the result against the pinned SHA-256.

The sections (token stream, HPAC, renderer, carrier, table) come out of the training and search pipeline at
https://github.com/RChang06/comma_joint_hops; this script only does the final lossless packing (RX1 model header,
BLK2 blocks with the recorded codec/transpose/brotli settings, stored zip) and refuses on any mismatch.
"""
import argparse, hashlib, io, json, lzma, struct, sys, zipfile
from pathlib import Path

import brotli

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from runtime import residual_archive as RA
from runtime.block_container import decode_model_blocks, transpose


def zip_p(p):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        info = zipfile.ZipInfo("p", date_time=(1980, 1, 1, 0, 0, 0))
        info.create_system = 3
        info.external_attr = 0o644 << 16
        z.writestr(info, p)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pieces", required=True, help="dir with plan.json, hpac.sec, renderer.sec, carrier.sec, table.bin, stream.bin")
    ap.add_argument("--out", default=str(HERE / "archive.zip"))
    a = ap.parse_args()
    d = Path(a.pieces)
    plan = json.loads((d / "plan.json").read_text())
    pieces = {k: (d / k).read_bytes() for k in plan["pieces_sha256"]}
    for k, v in pieces.items():
        if hashlib.sha256(v).hexdigest() != plan["pieces_sha256"][k]:
            sys.exit(f"refusing: {k} does not match its pinned sha256")
    hpac, sem, car = pieces["hpac.sec"], pieces["renderer.sec"], pieces["carrier.sec"]
    models = RA.RX1_MODEL_HEADER.pack(RA.RX1_MAGIC, *plan["rx1_header"], len(hpac), len(sem), len(car)) + hpac + sem + car
    tail = pieces["table.bin"] + pieces["stream.bin"]
    blocks = []
    for b in plan["blocks"]:
        data = models[b["start"]:b["end"]]
        if b["stride"]:
            data = transpose(data, b["stride"])
        if b["codec"] == 2:
            data = brotli.compress(data, **b["params"])
        elif b["codec"] == 1:
            data = lzma.compress(data, format=lzma.FORMAT_RAW, filters=[dict(id=lzma.FILTER_LZMA2, dict_size=1 << 20,
                                 preset=9 | lzma.PRESET_EXTREME, **b["params"])])
        tr = bytes((1, b["stride"])) if b["stride"] else b""
        blocks.append(bytes((b["codec"] | (128 if b["stride"] else 0),)) + len(data).to_bytes(3, "little") + tr + data)
    p = b"BLK2" + struct.pack("<IB", len(models), len(blocks)) + b"".join(blocks) + tail
    if decode_model_blocks(p) != (models, tail):
        sys.exit("refusing: block round trip failed")
    archive = zip_p(p)
    sha = hashlib.sha256(archive).hexdigest()
    if sha != plan["archive_sha256"] or len(archive) != plan["archive_bytes"]:
        sys.exit(f"refusing: rebuilt archive {len(archive)} B sha {sha} does not match the pinned one")
    Path(a.out).write_bytes(archive)
    print(f"archive.zip {len(archive):,} B sha256 {sha} -> {a.out}")


if __name__ == "__main__":
    main()
