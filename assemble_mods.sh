#!/usr/bin/env bash
# Assemble curated Contra mod trees for MacPatch.
# Thin wrapper: the tree layout lives in assemble_mods.py (bash 3.2 on macOS has no
# associative arrays, and the patch-over-base merge needs them).
#
#   ./assemble_mods.sh            # build
#   ./assemble_mods.sh --dry-run  # print the layout without touching anything
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$ROOT/assemble_mods.py" "$@"
