# GeneralsOnline-MacPatch

Community assets shipped to macOS players by the launcher. Packed by
`pack_upload.sh` into release zips and published on GitHub; the launcher downloads
those archives and merges them into the game install.

## Layout

The archive holds one directory per game. They are applied to **different** install
directories and must never be mixed.

```
GO_Mac_Patch/
├── Assets/            → Zero Hour   (the folder containing INIZH.big)
│   ├── *.big          eight archives: Control Bar Pro, HD control bar, decals, LAN lobby
│   ├── Data/          generals.csf for eleven languages
│   └── Maps/          ranked community maps
└── AssetsGenerals/    → Generals    (the folder with INI.big and no INIZH.big)
    ├── Art/Textures/  twelve Control Bar Pro textures
    ├── Data/INI/      ControlBarScheme.ini, MappedImages
    ├── Data/<Lang>/   generals.csf, Language.ini, HeaderTemplate.ini, CommandMap.ini
    ├── Window/        nine .wnd layouts
    └── GenTool/       fullviewport.dat
```

Zero Hour receives `.big` archives; Generals receives loose files. That difference is not
cosmetic — loose files take priority over archives, so anything landing in the wrong install
shadows that game's own data and breaks INI parsing on enums its executable does not know.

`fullviewport.dat` must contain the single byte `1`. The engine reads one byte and treats
anything other than `0` as enabled; an empty file silently disables full viewport.

## Locales

Both games get the same eleven languages, four files each: `generals.csf`, `Language.ini`
(fonts), `HeaderTemplate.ini` and `CommandMap.ini`.

`CommandMap.ini` is **not** interchangeable between the games, and neither is it optional.

It cannot be shared as-is: the Zero Hour file binds `TOGGLE_CAMERA_TRACKING_DRAWABLE`, a
command the Generals executable does not know, and `MetaMap::parseMetaMap` answers with
`throw INI_INVALID_DATA`. The Generals copies here are the Zero Hour files with that one
block removed; every other block and all seven fields are common to both executables.

It also cannot be left out. `GameEngine::init` loads `Data\<Language>\CommandMap` before the
shared `Data\INI\CommandMap`, and `INI::loadFileDirectory` ends with `throw
INI_CANT_OPEN_FILE` when nothing was read. The second path never gets a chance, so a missing
per-language file crashes the game exactly like a malformed one. English survives only
because the stock archives already carry `Data\English\CommandMap.ini`.

Where a translation lacks a label the engine shows `MISSING: '<label>'` rather than falling
back to English. Campaign subtitles are the exception: `doSpeechPlay` checks the lookup and
skips the subtitle instead. That guard exists in Zero Hour only, because classic Generals has
no subtitle system at all.

## Mods

Mods are separate release assets, never part of `GO_Mac_Patch.zip`. Each one unpacks into
its own `<install>/Mods/<id>/`, next to the game folders, and the engine picks it up through
`-mod <install>/Mods/<id>/config.json`.

| Mod | Content | Release assets |
|---|---|---|
| Contra 007 / 008 / 009 | `.big` | one zip each |
| Contra X | `.big` | three zips |
| Apocalptic | loose files | one zip |
| Silent Death | `.big` + loose files | four zips |
| ShockWave | `.big` + movies | one zip |
| Rise of the Reds | `.big` + movie | one zip |

A mod fits this scheme only when it is pure data: BIG archives, loose INI and maps, movies.
Anything that needs a patched Windows executable, a DLL hook or GenTool cannot run here.

### ShockWave and Rise of the Reds

Both come from SWR Productions and both install over Zero Hour 1.04; neither is built on the
other. Neither has been run in the game yet.

ModDB ships them as Clickteam Install Creator executables, which `unar` and `7z` cannot open.
[cicdec](https://github.com/Bioruebe/cicdec) can, under Mono:

```sh
mono cicdec.exe downloads/files/ShockWaveV1201/ShockWaveV1201.exe downloads/files/ShockWave_1.201
```

The installers carry the retail `generals.exe`, WorldBuilder, SWR.net and a small launcher;
none of that is packaged. The launcher's file map (`Shockwave_Lnchr.dat`,
`ROTR185_Lnchr.dat`) is the actual install recipe, and the trees reproduce it: `*.gib` are
plain `BIGF` archives renamed to `*.big` on launch, `Install_Final_*.bmp` replaces the splash,
and the stock `Data\Scripts` are hidden, which is `maskBaseScripts` here. The `!` prefixes
follow the same scheme as Contra, so `assemble_mods.py` layers them as is.

**ShockWave 1.201 + Hotfix v6.** Sources:
[ShockWave Version 1.201](https://www.moddb.com/mods/cc-shockwave/downloads/shockwave-version-12),
[ShockWave 1.201 Hotfix v6](https://www.moddb.com/mods/cc-shockwave/addons/shockwave-1201-hotfix).

- 11 archives, 10 movies in `Data/Movies`. The hotfix is a community addon
  (`moddb_dev`): Nuke General AI, challenge maps, pathfinder texture on snow maps.
- Classic cameos (`!!Shw_cicons`, `!!0ShwPtchIcon`) are a launcher option that is off by
  default, and are left out.
- Several INI values do not fit their fields: `SpawnReplaceDelay = 9999999999999999999` on
  three China squads, `RecenterTime`, `FuelLifetime`, `ClipReloadTime`. The `std::from_chars`
  parser throws `INI_INVALID_DATA` on them
  ([TheSuperHackers#2804](https://github.com/TheSuperHackers/GeneralsGameCode/issues/2804)).
  `GENERALS_ONLINE_DISABLE_STD_FROM_CHARS_PARSING` keeps the engine on `sscanf`, which
  accepts them; dropping that define breaks ShockWave.
- `OCL_AmericaSupplyDropZoneCrateDrop` delivers `SupplyDropZoneCrate_Dummy`, with the real
  `SupplyDropZoneCrate` commented out. That is SWR's own 1.201 data, not a repack error.
  GenLauncherGO players report that USA supply drop zones deliver nothing and swap the lines
  ([zero-hour-generals-online-shockwave-fix](https://github.com/Ronin12893/zero-hour-generals-online-shockwave-fix)).
  The tree keeps SWR's version until a run shows the same on this engine.
- [ControlBarPro SHW](https://www.moddb.com/mods/cc-shockwave/addons/controlbarpro-shw) is
  layered on top. Its schemes cover all 17 ShockWave sides, including the Armor, Salvage and
  Special Weapons generals, but its `InGameUI.ini` is built on stock Zero Hour: it reverts
  eight of ShockWave's special power radius cursors and only moves `MessagePosition` down to
  clear the GenTool overlay, which this engine does not draw. ShockWave's own file is
  therefore unpacked from `!Shw_ini` as loose `Data/INI/InGameUI.ini`, which outranks every
  archive of the mod.

**Rise of the Reds 1.85 + Patch 1.86.** Sources:
[Rise of the Reds Version 1.85](https://www.moddb.com/mods/rise-of-the-reds/downloads/rise-of-the-reds-version-185),
[ROTR Patch 1.86](https://www.moddb.com/mods/rise-of-the-reds/downloads/rotr-patch-186-release).

- 14 archives, 1.86 replaces four of them (`!!Rotr_Patch`, `!Rotr_AI`, `!Rotr_English`,
  `!Rotr_INI`). The splash comes from 1.86, which differs from 1.85.
- `00000000.016_` / `00000000.256_` are the mod's splash bitmaps, renamed by its launcher.
- [ControlBarPro ROTR](https://www.moddb.com/mods/rise-of-the-reds/addons/controlbarpro-rotr)
  is layered on top as is: its `InGameUI.ini` is byte-identical to 1.86, and it draws the
  Russian and ECA bars on the `AmericaLaserGeneral` and `AmericaSuperWeaponGeneral` sides,
  which is where 1.86 puts those factions.
- 1.87 is not on ModDB: SWR hands it out on its forum after registration. The map pack
  installers (`ROTRMapPack_V2.exe`, `ROTRMapPackUpdate.exe`) are not unpacked.
- Mods, RotR among them, are reported to hit an open audio crash or freeze
  ([TheSuperHackers#256](https://github.com/TheSuperHackers/GeneralsGameCode/issues/256)).

## Credits

The Generals control bar is Control Bar Pro, the classic-Generals build by Lithium,
distributed by the community through GenPatcher.

The locales are community builds, not stock game files: font settings carry Patch 1.04p
tweaks credited to xezon in `Language.ini`, and the string tables are extended with names of
the ranked community maps shipped here plus tooltips for the modified control bar.

## Publishing

GitHub workflow (release `v1.0`):

```sh
./download_unpack.sh          # download + unpack (Patch and/or mods)
# …edit GO_Mac_Patch / GO_Mac_Mod_* …
./pack_upload.sh              # pack + upload
```

Selective: `./download_unpack.sh Patch Contra007`, `./pack_upload.sh --no-upload ContraX`.

Local mod assembly from raw sources (`downloads/files`): `./assemble_mods.sh`.

Requires `gh` authenticated against `Okladnoj/GeneralsOnline-MacPatch`.
