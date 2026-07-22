# GeneralsOnline-MacPatch

Community assets shipped to macOS players by the launcher. Packed by
`pack_upload_patch.sh` into `GO_Mac_Patch.zip` and published as a GitHub release; the
launcher downloads that archive and merges it into the game install.

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

## Credits

The Generals control bar is Control Bar Pro, the classic-Generals build by Lithium,
distributed by the community through GenPatcher.

The locales are community builds, not stock game files: font settings carry Patch 1.04p
tweaks credited to xezon in `Language.ini`, and the string tables are extended with names of
the ranked community maps shipped here plus tooltips for the modified control bar.

## Publishing

```sh
./pack_upload_patch.sh
```

Requires `gh` authenticated against `Okladnoj/GeneralsOnline-MacPatch`.
