#!/usr/bin/env bash
# Replaces vendor/mermaiden and vendor/mermaiden-toolkit with packed copies from a Mermaiden
# checkout. MERMAIDEN_DIR names it; see README.md next to this script.
set -euo pipefail
dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
src="${MERMAIDEN_DIR:-$HOME/local/src/mermaiden}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

[ -d "$src/packages" ] || { echo "no Mermaiden checkout at $src" >&2; exit 1; }
if [ -n "$(git -C "$src" status --porcelain -- packages)" ]; then
  echo "warning: $src has uncommitted changes under packages/; SOURCE will name HEAD anyway" >&2
fi
(cd "$src" && pnpm run build:packages)

for pkg in mermaiden mermaiden-toolkit; do
  version="$(node -p 'require(process.argv[1]).version' "$src/packages/$pkg/package.json")"
  (cd "$src/packages/$pkg" && pnpm pack --pack-destination "$work" >/dev/null)
  rm -rf "$dir/$pkg" "$work/unpack"
  mkdir -p "$work/unpack"
  tar -xzf "$work/$pkg-$version.tgz" -C "$work/unpack"
  mv "$work/unpack/package" "$dir/$pkg"
done

git -C "$src" log -1 --format='commit %H%ncommitted %cI%nsubject %s' > "$dir/SOURCE"
echo "vendored mermaiden and mermaiden-toolkit from $(sed -n 1p "$dir/SOURCE")"
