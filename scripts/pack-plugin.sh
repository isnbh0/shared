#!/usr/bin/env bash
set -euo pipefail
name="${1:?usage: pack-plugin.sh <plugin-name>}"
src="plugins/${name}"
[ -d "$src" ] || { echo "no such plugin: $src" >&2; exit 1; }
out_dir="${2:-$(pwd)}"
mkdir -p "$out_dir"
out="$(cd "$out_dir" && pwd)/${name}.zip"
rm -f "$out"
( cd "$src" && zip -r "$out" . \
  -x "*.DS_Store" \
     "*/__pycache__/*" \
     "*.pyc" \
     "*.pyo" \
     "*/.pytest_cache/*" \
     "*/target/*" )
echo "wrote $out"
