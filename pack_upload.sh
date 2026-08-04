#!/bin/bash
# Pack local trees into release zips and upload to GitHub.
#
# Trees: GO_Mac_Patch/, GO_Mac_Mod_Contra007|008|009|ContraX|Apocalptic|Silent_Death/
# Split mods ship numbered parts: ContraX → .{1,2,3}.zip (contrax_parts.sh),
# Silent_Death → .{1,2,3,4}.zip (silent_death_parts.sh).
#
# Usage:
#   ./pack_upload.sh                  # everything, pack + upload
#   ./pack_upload.sh --no-upload      # zip only
#   ./pack_upload.sh Patch Contra007
#   ./pack_upload.sh Silent_Death --no-upload
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck source=contrax_parts.sh
source ./contrax_parts.sh
# shellcheck source=silent_death_parts.sh
source ./silent_death_parts.sh

REPO="${REPO:-Okladnoj/GeneralsOnline-MacPatch}"
TAG="${TAG:-v1.0}"
MAX_BYTES=$((2 * 1024 * 1024 * 1024))
UPLOAD=1

TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --no-upload) UPLOAD=0 ;;
    --upload) UPLOAD=1 ;;
    Patch|GO_Mac_Patch) TARGETS+=(Patch) ;;
    Contra007|Contra008|Contra009|ContraX|Apocalptic|Silent_Death) TARGETS+=("$arg") ;;
    *)
      echo "unknown target: $arg (Patch Contra007 Contra008 Contra009 ContraX Apocalptic Silent_Death)" >&2
      exit 1
      ;;
  esac
done

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=(Patch Contra007 Contra008 Contra009 ContraX Apocalptic Silent_Death)
fi

status=0

pack_dir() {
  local dir="$1"
  local zip="$2"
  local need_config="${3:-0}"

  if [[ ! -d "$dir" ]]; then
    echo "missing $dir — run ./download_unpack.sh or ./assemble_mods.sh first" >&2
    exit 1
  fi
  if [[ "$need_config" == "1" && ! -f "$dir/config.json" ]]; then
    echo "missing $dir/config.json" >&2
    exit 1
  fi

  echo "📦 Packing $dir → $zip ..."
  rm -f "$zip"
  (cd "$dir" && zip -r "../$zip" . -x "*.DS_Store")

  local size
  size=$(stat -f%z "$zip")
  echo "   size: $size bytes"

  if (( size >= MAX_BYTES )); then
    echo "❌ $zip is >= 2 GiB" >&2
    status=1
    return 1
  fi

  if (( UPLOAD )); then
    echo "📤 Uploading $zip → $REPO@$TAG ..."
    gh release upload "$TAG" "$zip" --repo "$REPO" --clobber
  fi
}

pack_contrax_parts() {
  local tree="GO_Mac_Mod_ContraX"
  if [[ ! -d "$tree" ]]; then
    echo "missing $tree" >&2
    exit 1
  fi
  if [[ ! -f "$tree/config.json" ]]; then
    echo "missing $tree/config.json" >&2
    exit 1
  fi

  local part files zip rel
  for part in 1 2 3; do
    case "$part" in
      1) files=("${CONTRAX_PART1[@]}") ;;
      2) files=("${CONTRAX_PART2[@]}") ;;
      3) files=("${CONTRAX_PART3[@]}") ;;
    esac
    zip="GO_Mac_Mod_ContraX.$part.zip"
    echo "📦 Packing $tree → $zip (part $part) ..."
    rm -f "$zip"
    (
      cd "$tree"
      for rel in "${files[@]}"; do
        if [[ ! -e "$rel" ]]; then
          echo "missing $tree/$rel (needed for part $part)" >&2
          exit 1
        fi
      done
      zip -r "../$zip" "${files[@]}" -x "*.DS_Store"
    )

    local size
    size=$(stat -f%z "$zip")
    echo "   size: $size bytes"
    if (( size >= MAX_BYTES )); then
      echo "❌ $zip is >= 2 GiB" >&2
      status=1
      continue
    fi
    if (( UPLOAD )); then
      echo "📤 Uploading $zip → $REPO@$TAG ..."
      gh release upload "$TAG" "$zip" --repo "$REPO" --clobber
    fi
  done
}

pack_parts() {
  local tree="$1"
  local prefix="$2"
  local count="$3"

  if [[ ! -d "$tree" ]]; then
    echo "missing $tree — run ./assemble_mods.sh first" >&2
    exit 1
  fi
  if [[ ! -f "$tree/config.json" ]]; then
    echo "missing $tree/config.json" >&2
    exit 1
  fi

  local part files zip rel
  for (( part = 1; part <= count; part++ )); do
    eval "files=(\"\${${prefix}_PART${part}[@]}\")"
    zip="$tree.$part.zip"
    echo "📦 Packing $tree → $zip (part $part) ..."
    rm -f "$zip"
    (
      cd "$tree"
      for rel in "${files[@]}"; do
        if [[ ! -e "$rel" ]]; then
          echo "missing $tree/$rel (needed for part $part)" >&2
          exit 1
        fi
      done
      zip -qr "../$zip" "${files[@]}" -x "*.DS_Store"
    )

    local size
    size=$(stat -f%z "$zip")
    echo "   size: $size bytes"
    if (( size >= MAX_BYTES )); then
      echo "❌ $zip is >= 2 GiB" >&2
      status=1
      continue
    fi
    if (( UPLOAD )); then
      echo "📤 Uploading $zip → $REPO@$TAG ..."
      gh release upload "$TAG" "$zip" --repo "$REPO" --clobber
    fi
  done
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    Patch) pack_dir GO_Mac_Patch GO_Mac_Patch.zip 0 ;;
    Contra007|Contra008|Contra009|Apocalptic) pack_dir "GO_Mac_Mod_$t" "GO_Mac_Mod_$t.zip" 1 ;;
    ContraX) pack_contrax_parts ;;
    Silent_Death) pack_parts GO_Mac_Mod_Silent_Death SILENT_DEATH 4 ;;
  esac
done

if (( status == 0 )); then
  if (( UPLOAD )); then
    echo "✅ Done! Packed and uploaded."
  else
    echo "✅ Done! Packed (no upload)."
  fi
else
  echo "⚠️  Finished with errors." >&2
fi
exit "$status"
