#!/bin/bash
# Shared ContraX release-part file lists (relative to GO_Mac_Mod_ContraX/).
# Sourced by assemble_mods.sh and repack_upload.sh.
# Rules: no overlap; config.json only in part 1; each zip stays under 2 GiB.

CONTRAX_PART1=(
  config.json
  GenArial.ttf
  Install_Final.bmp
  00_INI.big
  01_AI.big
  02_GameData.big
  03_W3D.big
  05_Terrain.big
  06_Window.big
  08_Textures.big
  11_HotkeysOriginal_English.big
  12_ControlBarPro.big
  13_CameosHD.big
)

CONTRAX_PART2=(
  07_Maps.big
  09_MusicEnhanced.big
  50_Textures.big
  51_ControlBarPro.big
  52_Patch1.big
  53_HotkeysOriginal_English.big
  54_CameosHD.big
  55_DisableFogEffects.big
)

CONTRAX_PART3=(
  04_Audio.big
  10_UnitVoicesEnglish.big
)
