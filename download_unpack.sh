#!/bin/bash
# Download release assets from GitHub and unpack into local trees.
#
# Usage:
#   ./download_unpack.sh                 # Patch + all mods
#   ./download_unpack.sh Patch Contra007
#   ./download_unpack.sh ContraX
set -euo pipefail

cd "$(dirname "$0")"

REPO="${REPO:-Okladnoj/GeneralsOnline-MacPatch}"
TAG="${TAG:-v1.0}"

TARGETS=()
for arg in "$@"; do
  case "$arg" in
    Patch|GO_Mac_Patch) TARGETS+=(Patch) ;;
    Contra007|Contra008|Contra009|ContraX) TARGETS+=("$arg") ;;
    *)
      echo "unknown target: $arg (Patch Contra007 Contra008 Contra009 ContraX)" >&2
      exit 1
      ;;
  esac
done

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=(Patch Contra007 Contra008 Contra009 ContraX)
fi

download_unzip() {
  local zip="$1"
  local dest="$2"

  echo "📥 Downloading $zip (release $TAG)..."
  gh release download "$TAG" -p "$zip" --repo "$REPO" --clobber

  echo "📦 Unpacking into $dest/ ..."
  rm -rf "$dest"
  mkdir "$dest"
  unzip -qo "$zip" -d "$dest"
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    Patch)
      download_unzip GO_Mac_Patch.zip GO_Mac_Patch
      ;;
    Contra007|Contra008|Contra009)
      download_unzip "GO_Mac_Mod_$t.zip" "GO_Mac_Mod_$t"
      if [[ ! -f "GO_Mac_Mod_$t/config.json" ]]; then
        echo "missing GO_Mac_Mod_$t/config.json" >&2
        exit 1
      fi
      ;;
    ContraX)
      echo "📥 Downloading GO_Mac_Mod_ContraX.{1,2,3}.zip (release $TAG)..."
      gh release download "$TAG" -p "GO_Mac_Mod_ContraX.1.zip" --repo "$REPO" --clobber
      gh release download "$TAG" -p "GO_Mac_Mod_ContraX.2.zip" --repo "$REPO" --clobber
      gh release download "$TAG" -p "GO_Mac_Mod_ContraX.3.zip" --repo "$REPO" --clobber

      echo "📦 Merging parts into GO_Mac_Mod_ContraX/ ..."
      rm -rf GO_Mac_Mod_ContraX
      mkdir GO_Mac_Mod_ContraX
      unzip -qo GO_Mac_Mod_ContraX.1.zip -d GO_Mac_Mod_ContraX
      unzip -qo GO_Mac_Mod_ContraX.2.zip -d GO_Mac_Mod_ContraX
      unzip -qo GO_Mac_Mod_ContraX.3.zip -d GO_Mac_Mod_ContraX

      if [[ ! -f GO_Mac_Mod_ContraX/config.json ]]; then
        echo "missing GO_Mac_Mod_ContraX/config.json after merge" >&2
        exit 1
      fi
      ;;
  esac
done

echo "✅ Done! Unpacked under GO_Mac_Patch/ and/or GO_Mac_Mod_*/"
