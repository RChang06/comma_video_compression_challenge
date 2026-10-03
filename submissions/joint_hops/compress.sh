#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# usage: compress.sh <pieces_dir>   (pieces: https://github.com/RChang06/comma_joint_hops, folder pieces/)
python "$HERE/compress.py" --pieces "$1" --out "$HERE/archive.zip"
