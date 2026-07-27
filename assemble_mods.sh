#!/usr/bin/env bash
# Assemble curated Contra mod trees for MacPatch.
# Hardlinks save disk; numeric BIG prefixes = load order (last wins under overwrite=TRUE).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/downloads/files"

hl() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  rm -f "$dest"
  ln "$src" "$dest"
}

echo "==> Contra007"
DST="$ROOT/GO_Mac_Mod_Contra007"
rm -rf "$DST"
mkdir -p "$DST/Data/INI" "$DST/Data/Scripts" "$DST/Maps"

hl "$SRC/Contra007/!Contra007.big"            "$DST/00_Contra007.big"
hl "$SRC/Contra007/!Contra007-en.big"         "$DST/01_Contra007-en.big"
hl "$SRC/Contra007/!Contra006Music.big"       "$DST/02_Contra006Music.big"
hl "$SRC/!Contra-007-Fix.big"                 "$DST/03_Contra-007-Fix.big"
hl "$SRC/Contra007/ariag.ttf"                 "$DST/ariag.ttf"
hl "$SRC/Contra007/Install_Final.bmp"         "$DST/Install_Final.bmp"
hl "$SRC/Contra007/00000000.016"              "$DST/00000000.016"
hl "$SRC/Contra007/00000000.256"              "$DST/00000000.256"
hl "$SRC/Generals Zero Hour/Data/INI/GameData.ini" \
                                              "$DST/Data/INI/GameData.ini"
hl "$SRC/Generals Zero Hour/Data/Scripts/SkirmishScripts.scb" \
                                              "$DST/Data/Scripts/SkirmishScripts.scb"
hl "$SRC/Maps/MapCache.ini"                   "$DST/Maps/MapCache.ini"

cat >"$DST/config.json" <<'EOF'
{
  "id": "contra007",
  "displayName": "Contra 007",
  "version": "0.07.1",
  "baseGame": "zh",
  "online": true,
  "maskBaseScripts": true,
  "description": "Curated Contra 007 (EN) + Fix + NetFix + Fixed AI scripts + MapFix cache",
  "author": "Contra Mod Team / curated for macOS",
  "bigGlob": "*.big",
  "approxSizeMB": 300
}
EOF

echo "==> Contra008"
DST="$ROOT/GO_Mac_Mod_Contra008"
rm -rf "$DST"
mkdir -p "$DST"

hl "$SRC/Contra008FINAL/!Contra008.ctr"         "$DST/00_Contra008.big"
hl "$SRC/Contra008FINAL/!Contra008EN.ctr"       "$DST/01_Contra008EN.big"
hl "$SRC/Contra008FINAL/!Contra008VLoc.ctr"     "$DST/02_Contra008VLoc.big"
hl "$SRC/Contra008FINAL/!Contra008MNew.ctr"     "$DST/03_Contra008MNew.big"
hl "$SRC/Contra008FINAL/Install_Final_Contra.bmp" "$DST/Install_Final.bmp"

cat >"$DST/config.json" <<'EOF'
{
  "id": "contra008",
  "displayName": "Contra 008",
  "version": "8.0.0",
  "baseGame": "zh",
  "online": true,
  "maskBaseScripts": true,
  "description": "Curated Contra 008 Final (EN, localized VO, new music)",
  "author": "Contra Mod Team / curated for macOS",
  "bigGlob": "*.big",
  "approxSizeMB": 970
}
EOF

echo "==> Contra009"
DST="$ROOT/GO_Mac_Mod_Contra009"
rm -rf "$DST"
mkdir -p "$DST"

hl "$SRC/Contra009Final/!Contra009Final.ctr"           "$DST/00_Contra009Final.big"
hl "$SRC/Contra009Final/!Contra009Final_EN.ctr"        "$DST/01_Contra009Final_EN.big"
hl "$SRC/Contra009Final/!Contra009Final_EngVO.ctr"     "$DST/02_Contra009Final_EngVO.big"
hl "$SRC/Contra009Final/!Contra009Final_NewMusic.ctr"  "$DST/03_Contra009Final_NewMusic.big"
hl "$SRC/Contra009Final/Install_Final_Contra.bmp"      "$DST/Install_Final.bmp"

hl "$SRC/Contra009FinalPatch1/!!Contra009Final_Patch1.ctr"        "$DST/10_Patch1.big"
hl "$SRC/Contra009FinalPatch1/!!Contra009Final_Patch1_EN.ctr"     "$DST/11_Patch1_EN.big"
hl "$SRC/Contra009FinalPatch1/!!Contra009Final_Patch1_EngVO.ctr"  "$DST/12_Patch1_EngVO.big"
hl "$SRC/Contra009FinalPatch1/GenArial.ttf"                       "$DST/GenArial.ttf"

hl "$SRC/Contra009FinalPatch2/!!!Contra009Final_Patch2.ctr"           "$DST/20_Patch2.big"
hl "$SRC/Contra009FinalPatch2/!!!Contra009Final_Patch2_EN.ctr"        "$DST/21_Patch2_EN.big"
hl "$SRC/Contra009FinalPatch2/!!!Contra009Final_Patch2_EngVO.ctr"     "$DST/22_Patch2_EngVO.big"
hl "$SRC/Contra009FinalPatch2/!!!Contra009Final_Patch2_GameData.ctr"  "$DST/23_Patch2_GameData.big"

hl "$SRC/Contra009FinalPatch3/!!!!Contra009Final_Patch3.ctr"              "$DST/30_Patch3.big"
hl "$SRC/Contra009FinalPatch3/!!!!Contra009Final_Patch3_EN_Leikeze.ctr"   "$DST/31_Patch3_EN_Leikeze.big"
hl "$SRC/Contra009FinalPatch3/!!!!Contra009Final_Patch3_EngVO.ctr"        "$DST/32_Patch3_EngVO.big"
hl "$SRC/Contra009FinalPatch3/!!!!Contra009Final_Patch3_GameData.ctr"     "$DST/33_Patch3_GameData.big"

hl "$SRC/Contra009FinalPatch3Hotfix4/!!!!!!!!Contra009Final_Patch3_Hotfix4.ctr" "$DST/40_Hotfix4.big"
hl "$SRC/Contra009FinalPatch3Hotfix4/!!!!Contra009Final_Patch3_EN_Leikeze.ctr"   "$DST/41_Hotfix4_EN_Leikeze.big"

cat >"$DST/config.json" <<'EOF'
{
  "id": "contra009",
  "displayName": "Contra 009",
  "version": "9.0.0-hf4",
  "baseGame": "zh",
  "online": true,
  "maskBaseScripts": true,
  "description": "Curated Contra 009 Final + Patch1–3 + Hotfix4 (EN Leikeze, EngVO, new music)",
  "author": "Contra Mod Team / curated for macOS",
  "bigGlob": "*.big",
  "approxSizeMB": 1800
}
EOF

echo "==> ContraX"
DST="$ROOT/GO_Mac_Mod_ContraX"
rm -rf "$DST"
mkdir -p "$DST"

hl "$SRC/ContraXBeta2/!ContraXBeta2_INI.ctr"              "$DST/00_INI.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_AI.ctr"               "$DST/01_AI.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_GameData.ctr"         "$DST/02_GameData.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_W3D.ctr"              "$DST/03_W3D.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_Audio.ctr"            "$DST/04_Audio.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_Terrain.ctr"          "$DST/05_Terrain.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_Window.ctr"           "$DST/06_Window.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_Maps.ctr"             "$DST/07_Maps.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_Textures.ctr"         "$DST/08_Textures.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_MusicEnhanced.ctr"    "$DST/09_MusicEnhanced.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_UnitVoicesEnglish.ctr" "$DST/10_UnitVoicesEnglish.big"
hl "$SRC/ContraXBeta2/!ContraXBeta2_HotkeysOriginal_English.ctr" "$DST/11_HotkeysOriginal_English.big"
hl "$SRC/ContraXBeta2/!!ContraXBeta2_ControlBarPro.ctr"  "$DST/12_ControlBarPro.big"
hl "$SRC/ContraXBeta2/!!ContraXBeta2_CameosHD.ctr"        "$DST/13_CameosHD.big"
hl "$SRC/ContraXBeta2/GenArial.ttf"                       "$DST/GenArial.ttf"
hl "$SRC/ContraXBeta2/Install_Final_Contra.bmp"           "$DST/Install_Final.bmp"

hl "$SRC/ContraXBeta2Patch1/!ContraXBeta2_Textures.ctr"              "$DST/50_Textures.big"
hl "$SRC/ContraXBeta2Patch1/!!ContraXBeta2_ControlBarPro.ctr"        "$DST/51_ControlBarPro.big"
hl "$SRC/ContraXBeta2Patch1/!!ContraXBeta2_Patch1.ctr"               "$DST/52_Patch1.big"
hl "$SRC/ContraXBeta2Patch1/!ContraXBeta2_HotkeysOriginal_English.ctr" "$DST/53_HotkeysOriginal_English.big"
hl "$SRC/ContraXBeta2Patch1/!!ContraXBeta2_CameosHD.ctr"             "$DST/54_CameosHD.big"
hl "$SRC/ContraXBeta2Patch1/!!ContraXBeta2_DisableFogEffects.ctr"    "$DST/55_DisableFogEffects.big"

cat >"$DST/config.json" <<'EOF'
{
  "id": "contrax",
  "displayName": "Contra X",
  "version": "x-beta2-p1",
  "baseGame": "zh",
  "online": true,
  "maskBaseScripts": true,
  "description": "Curated Contra X Beta 2 + Patch 1 (EN, Enhanced music, Control Bar Pro)",
  "author": "Contra Mod Team / curated for macOS",
  "bigGlob": "*.big",
  "approxSizeMB": 3200
}
EOF

# Three release parts (<2 GiB each). No filename overlap; config.json only in .1.
# Hardlinks from the unified tree above.
# shellcheck source=contrax_parts.sh
source "$ROOT/contrax_parts.sh"

echo "==> ContraX parts (.1 / .2 / .3)"
hl_from_tree() {
  local treedir="$1" part="$2" rel="$3"
  hl "$treedir/$rel" "$ROOT/GO_Mac_Mod_ContraX.$part/$rel"
}

for p in 1 2 3; do
  rm -rf "$ROOT/GO_Mac_Mod_ContraX.$p"
  mkdir -p "$ROOT/GO_Mac_Mod_ContraX.$p"
done

for rel in "${CONTRAX_PART1[@]}"; do hl_from_tree "$DST" 1 "$rel"; done
for rel in "${CONTRAX_PART2[@]}"; do hl_from_tree "$DST" 2 "$rel"; done
for rel in "${CONTRAX_PART3[@]}"; do hl_from_tree "$DST" 3 "$rel"; done

echo
echo "==> Summary"
for d in GO_Mac_Mod_Contra007 GO_Mac_Mod_Contra008 GO_Mac_Mod_Contra009 \
         GO_Mac_Mod_ContraX GO_Mac_Mod_ContraX.1 GO_Mac_Mod_ContraX.2 GO_Mac_Mod_ContraX.3; do
  echo "--- $d ---"
  du -sh "$ROOT/$d"
  echo -n "  files: "
  find "$ROOT/$d" -type f | wc -l | tr -d ' '
  if [[ "$d" == "GO_Mac_Mod_ContraX.1" || "$d" == GO_Mac_Mod_Contra00* || "$d" == "GO_Mac_Mod_ContraX" ]]; then
    test -f "$ROOT/$d/config.json"
  fi
  while IFS= read -r f; do
    mag=$(xxd -l 4 -p "$f")
    if [ "$mag" != "42494746" ]; then
      echo "WARN not BIGF: $f ($mag)" >&2
    fi
  done < <(find "$ROOT/$d" -name '*.big' -type f)
done
echo "Done."
