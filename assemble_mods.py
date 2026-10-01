#!/usr/bin/env python3
"""Assemble curated Contra mod trees for MacPatch.

Load priority is encoded in the numeric BIG prefix: the engine inserts mod archives
ahead of the install and walks them backwards, so 00_ outranks 01_. Contra encodes the
same priority with leading '!' - more '!' sorts earlier in a Windows directory listing,
which is why a patch outranks the base it is installed over. Numbering therefore follows
the ASCII order of the ORIGINAL archive names, and an archive whose original name repeats
in a later layer replaces the earlier one, exactly as copying the patch over the install
would on Windows.

Local edits (custom splash screens, patched textures) live in assets/<mod>/ and are
applied after the archives are linked, so re-running this script never loses them.
"""

import hashlib
import json
import os
import re
import shutil
import struct
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "downloads", "files")
ASSETS = os.path.join(ROOT, "assets")
CATALOG = os.path.join(ROOT, "..", "general_online_zh", "public", "api", "mods.json")
SITE_ARTWORK = os.path.join(os.path.dirname(CATALOG), "mods")
ARTWORK_KINDS = ("banner", "medallion")
RELEASE_BASE = "https://github.com/Okladnoj/GeneralsOnline-MacPatch/releases/latest/download"
BASE_PROFILES = {"zh": "z_generals"}

DRY_RUN = "--dry-run" in sys.argv
EMIT_CATALOG = "--catalog" in sys.argv
TARGETS = [a for a in sys.argv[1:] if not a.startswith("-")]


class Archive:
    def __init__(self, layer_dir, original, name, rank=None):
        self.layer_dir = layer_dir
        self.original = original
        self.name = name
        self.rank = rank or original

    @property
    def source(self):
        return os.path.join(SRC, self.layer_dir, self.original)


class Tree:
    """A mod that ships loose files rather than layered archives.

    Contra packs everything into .ctr archives, so its tree is built by naming and
    ordering them. Apocalptic and Silent Death are installed on Windows by copying a
    folder over the game directory, so the folder itself is the mod: it is linked as
    it stands, minus what cannot work here (Miles Sound System, editor leftovers).

    Renames exist because the engine skips NNN_*.big under a mod - those names belong
    to the community patch overlay. A mod archive that must load gets a two digit name.
    """

    SKIP_NAMES = (".DS_Store", "Thumbs.db", "desktop.ini")

    def __init__(self, source, skip_dirs=(), skip_suffixes=(), rename=None):
        self.source = source
        self.skip_dirs = set(skip_dirs)
        self.skip_suffixes = tuple(skip_suffixes)
        self.rename = rename or {}

    def files(self):
        """Yields (absolute source, path relative to the mod root)."""
        root = os.path.join(SRC, self.source)
        for current, dirs, names in os.walk(root):
            relative_dir = os.path.relpath(current, root)
            dirs[:] = sorted(d for d in dirs if d not in self.skip_dirs)

            for name in sorted(names):
                if name in self.SKIP_NAMES or name.endswith(self.skip_suffixes):
                    continue

                relative = name if relative_dir == "." else os.path.join(relative_dir, name)
                yield os.path.join(current, name), self.rename.get(relative, relative)


class Overlay:
    """Loose files a whole Windows install lays over the archives it loads.

    WW3 ships as a complete Zero Hour folder: the mod's archives plus some 25 000 loose
    files, most of them byte for byte copies of entries those archives already hold. A
    loose file is kept only when it changes what the engine reads - it is new, or it
    differs from the archive entry that would win without it. Paths the engine never
    reads (editor molds, the author's backups) are listed in skip.
    """

    def __init__(self, source, dirs, shadowing, skip=()):
        self.source = source
        self.dirs = dirs
        self.shadowing = shadowing
        self.skip = [re.compile(pattern, re.IGNORECASE) for pattern in skip]

    def files(self):
        """Yields (absolute source, path relative to the mod root)."""
        root = os.path.join(SRC, self.source)
        winners = self.winning_entries(root)

        for directory in self.dirs:
            for current, dirs, names in os.walk(os.path.join(root, directory)):
                dirs.sort()

                for name in sorted(names):
                    path = os.path.join(current, name)
                    relative = os.path.relpath(path, root)
                    if self.is_skipped(relative) or self.is_shadowed(path, relative, winners):
                        continue

                    yield path, relative

    def winning_entries(self, root):
        winners = {}
        for archive in self.shadowing:
            archive_path = os.path.join(root, archive)
            for name, offset, size in big_entries(archive_path):
                winners.setdefault(name.lower().replace("/", "\\"), (archive_path, offset, size))

        return winners

    def is_skipped(self, relative):
        return any(pattern.fullmatch(relative) for pattern in self.skip)

    @staticmethod
    def is_shadowed(path, relative, winners):
        entry = winners.get(relative.lower().replace("/", "\\"))
        if entry is None:
            return False

        archive_path, offset, size = entry
        if size != os.path.getsize(path):
            return False

        with open(archive_path, "rb") as archive, open(path, "rb") as loose:
            archive.seek(offset)
            return archive.read(size) == loose.read()


# Unofficial Control Bar Pro 2.1.1 rebuilt for Contra by Hojjat. Nine leading '!' put it
# ahead of every patch, which is what lets it replace the mod's own control bar layout.
def control_bar_pro_layer():
    return [
        Archive("ControlBarPro_Contra_v2_1_1",
                "!!!!!!!!!ControlBarPro_Contra.big", "ControlBarPro_Contra"),
    ]


CONTROL_BAR_PRO_ZH = "ControlBarProZH_v1.2_1920x1080"


def control_bar_pro_zh_layer():
    originals = [f"340_ControlBarPro{part}.big" for part in ("ZH", "1080ZH", "Data1080ZH", "Art1080ZH")]
    return [
        Archive(CONTROL_BAR_PRO_ZH, original, original[4:-4], rank="!" * 10 + original)
        for original in originals
    ]


CONTRA008_TREE = os.path.relpath(os.path.join(ROOT, "GO_Mac_Mod_Contra008"), SRC)


def control_bar_pro_18_buttons_layer():
    contra = control_bar_pro_layer()[0]
    return [
        Archive(CONTRA008_TREE, f"00_{contra.name}.big", contra.name, rank=contra.original),
    ]


PATCH_ASSETS = os.path.relpath(os.path.join(ROOT, "GO_Mac_Patch", "Assets"), SRC)


def control_bar_hd_layer():
    return [
        Archive(PATCH_ASSETS, f"400_ControlBarHD{part}ZH.big", f"ControlBarHD{part}ZH")
        for part in ("Base", "English")
    ]


def contra009_layers():
    final = "Contra009Final"
    p1, p2, p3 = "Contra009FinalPatch1", "Contra009FinalPatch2", "Contra009FinalPatch3"
    hf3 = "Contra009FinalPatch3Hotfix3.1"
    hf4 = "Contra009FinalPatch3Hotfix4"
    return [
        [
            Archive(final, "!Contra009Final.ctr", "Contra009Final"),
            Archive(final, "!Contra009Final_EN.ctr", "Contra009Final_EN"),
            Archive(final, "!Contra009Final_EngVO.ctr", "Contra009Final_EngVO"),
            Archive(final, "!Contra009Final_NewMusic.ctr", "Contra009Final_NewMusic"),
        ],
        [
            Archive(p1, "!!Contra009Final_Patch1.ctr", "Patch1"),
            Archive(p1, "!!Contra009Final_Patch1_EN.ctr", "Patch1_EN"),
            Archive(p1, "!!Contra009Final_Patch1_EngVO.ctr", "Patch1_EngVO"),
        ],
        [
            Archive(p2, "!!!Contra009Final_Patch2.ctr", "Patch2"),
            Archive(p2, "!!!Contra009Final_Patch2_EN.ctr", "Patch2_EN"),
            Archive(p2, "!!!Contra009Final_Patch2_EngVO.ctr", "Patch2_EngVO"),
            Archive(p2, "!!!Contra009Final_Patch2_GameData.ctr", "Patch2_GameData"),
        ],
        [
            Archive(p3, "!!!!Contra009Final_Patch3.ctr", "Patch3"),
            Archive(p3, "!!!!Contra009Final_Patch3_EN_Leikeze.ctr", "Patch3_EN_Leikeze"),
            Archive(p3, "!!!!Contra009Final_Patch3_EngVO.ctr", "Patch3_EngVO"),
            Archive(p3, "!!!!Contra009Final_Patch3_GameData.ctr", "Patch3_GameData"),
        ],
        [
            Archive(hf3, "!!!!!!!Contra009Final_Patch3_Hotfix3.ctr", "Patch3_Hotfix3"),
            Archive(hf3, "!!!!!!!Contra009Final_Patch3_Hotfix3_AI.ctr", "Patch3_Hotfix3_AI"),
            Archive(hf3, "!!!!Contra009Final_Patch3_EN_Leikeze.ctr", "Patch3_EN_Leikeze"),
        ],
        [
            Archive(hf4, "!!!!!!!!Contra009Final_Patch3_Hotfix4.ctr", "Patch3_Hotfix4"),
            Archive(hf4, "!!!!Contra009Final_Patch3_EN_Leikeze.ctr", "Patch3_EN_Leikeze"),
        ],
        control_bar_pro_layer(),
    ]


def contrax_layers():
    base, p1 = "ContraXBeta2", "ContraXBeta2Patch1"
    return [
        [
            Archive(base, "!ContraXBeta2_INI.ctr", "INI"),
            Archive(base, "!ContraXBeta2_AI.ctr", "AI"),
            Archive(base, "!ContraXBeta2_GameData.ctr", "GameData"),
            Archive(base, "!ContraXBeta2_W3D.ctr", "W3D"),
            Archive(base, "!ContraXBeta2_Audio.ctr", "Audio"),
            Archive(base, "!ContraXBeta2_Terrain.ctr", "Terrain"),
            Archive(base, "!ContraXBeta2_Window.ctr", "Window"),
            Archive(base, "!ContraXBeta2_Maps.ctr", "Maps"),
            Archive(base, "!ContraXBeta2_Textures.ctr", "Textures"),
            Archive(base, "!ContraXBeta2_MusicEnhanced.ctr", "MusicEnhanced"),
            Archive(base, "!ContraXBeta2_UnitVoicesEnglish.ctr", "UnitVoicesEnglish"),
            Archive(base, "!ContraXBeta2_HotkeysOriginal_English.ctr", "HotkeysOriginal_English"),
            Archive(base, "!!ContraXBeta2_ControlBarPro.ctr", "ControlBarPro"),
            Archive(base, "!!ContraXBeta2_CameosHD.ctr", "CameosHD"),
        ],
        [
            Archive(p1, "!!ContraXBeta2_Patch1.ctr", "Patch1"),
            Archive(p1, "!ContraXBeta2_Textures.ctr", "Textures"),
            Archive(p1, "!ContraXBeta2_HotkeysOriginal_English.ctr", "HotkeysOriginal_English"),
            Archive(p1, "!!ContraXBeta2_ControlBarPro.ctr", "ControlBarPro"),
            Archive(p1, "!!ContraXBeta2_CameosHD.ctr", "CameosHD"),
            Archive(p1, "!!ContraXBeta2_DisableFogEffects.ctr", "DisableFogEffects"),
        ],
    ]


CONTRAX_TREE = os.path.relpath(os.path.join(ROOT, "GO_Mac_Mod_ContraX"), SRC)


def contrax_brutal_layers():
    merged = {a.original: a for layer in contrax_layers() for a in layer}
    built = [f"{i:02d}_{merged[key].name}.big" for i, key in enumerate(sorted(merged))]
    return [
        [Archive(CONTRAX_TREE, name, name[3:-4]) for name in built],
        [
            Archive(".", "!!!!!ContraXBeta2Patch1BossReplacerv_2.1.13.big", "BossReplacer"),
        ],
    ]


def loose_files(source, dest):
    root = os.path.join(SRC, source)
    if not os.path.isdir(root):
        return [(source, dest)]

    return [
        (os.path.join(source, relative), os.path.join(dest, relative))
        for current, _dirs, names in sorted(os.walk(root))
        for relative in sorted(os.path.relpath(os.path.join(current, name), root) for name in names)
        if os.path.basename(relative) not in Tree.SKIP_NAMES
    ]


TEOD_MOVIES = [
    f"Comp_{general}Gen_{variant}000.bik"
    for general in ("Air", "Demol", "Infantry", "Laser", "Nuke", "Stealth", "Super", "Tank", "Thrax")
    for variant in ("", "inv_")
] + [f"{portrait}{side}.bik" for portrait in ("haf", "ruaf", "smf") for side in ("L", "R")]


def shockwave_layers():
    base, hotfix = "ShockWave_1.201", "Shw_1.201_Hotfix_v6"
    spe = "Shockwave_Sinple_Player_Experience_2.1.3"
    return [
        [
            Archive(base, "!0Shwpatch.gib", "Shwpatch"),
            Archive(base, "!Shw2DArt.gib", "2DArt"),
            Archive(base, "!ShwAudio.gib", "Audio"),
            Archive(base, "!ShwTextures.gib", "Textures"),
            Archive(base, "!ShwVoice.gib", "Voice"),
            Archive(base, "!ShwW3D.gib", "W3D"),
            Archive(base, "!Shw_Challenge.gib", "Challenge"),
            Archive(base, "!Shw_ini.gib", "INI"),
            Archive(base, "!Shw_maps.gib", "Maps"),
            Archive(base, "!Shw_scripts.gib", "Scripts"),
            Archive(base, "!Shw_wnd.gib", "Window"),
        ],
        [
            Archive(hotfix, "!!!!!0Shw12HotfixV6-Fixes.big", "HotfixV6_Fixes"),
        ],
        [
            Archive(spe, "!ShwAudio.gib", "Audio"),
            Archive(spe, "!Shw_Challenge.gib", "Challenge"),
            Archive(spe, "!Shw_ini.gib", "INI"),
        ],
        [
            Archive("ControlBarPro_SHW.1", "!!!!!ControlBarPro SHW.big", "ControlBarPro_SHW"),
        ],
    ]


def rotr_layers():
    base, patch = "ROTR_1.85", "ROTR_1.86"
    return [
        [
            Archive(base, "!!Rotr_Patch.gib", "Patch"),
            Archive(base, "!Rotr_2D.gib", "2D"),
            Archive(base, "!Rotr_AI.gib", "AI"),
            Archive(base, "!Rotr_Audio.gib", "Audio"),
            Archive(base, "!Rotr_Blckr.gib", "Blocker"),
            Archive(base, "!Rotr_English.gib", "English"),
            Archive(base, "!Rotr_INI.gib", "INI"),
            Archive(base, "!Rotr_Maps.gib", "Maps"),
            Archive(base, "!Rotr_Music.gib", "Music"),
            Archive(base, "!Rotr_Terrain.gib", "Terrain"),
            Archive(base, "!Rotr_Textures.gib", "Textures"),
            Archive(base, "!Rotr_Voice.gib", "Voice"),
            Archive(base, "!Rotr_W3D.gib", "W3D"),
            Archive(base, "!Rotr_Window.gib", "Window"),
        ],
        [
            Archive(patch, "!!Rotr_Patch.gib", "Patch"),
            Archive(patch, "!Rotr_AI.gib", "AI"),
            Archive(patch, "!Rotr_English.gib", "English"),
            Archive(patch, "!Rotr_INI.gib", "INI"),
        ],
        [
            Archive(".", "!!!!!ROTR_ControlBarPro.gib", "ControlBarPro_RotR"),
        ],
    ]


WW3_ARCHIVES = [f"00PMBeta{number}.big" for number in range(993, 1000)]
ZH_ARCHIVES = [
    "AudioEnglishZH.big", "AudioZH.big", "EnglishZH.big", "GensecZH.big", "INIZH.big",
    "MapsZH.big", "Music.big", "MusicZH.big", "ShadersZH.big", "SpeechEnglishZH.big",
    "SpeechZH.big", "TerrainZH.big", "TexturesZH.big", "W3DEnglishZH.big", "W3DZH.big",
    "WindowZH.big",
]


def ww3_overlay():
    return Overlay(
        "WW3_Mod",
        dirs=["Art", "Audio", "Data", "Maps", "Window"],
        shadowing=WW3_ARCHIVES + ZH_ARCHIVES,
        skip=[
            r"Data/Editor/.+",
            r"Data/Scripts/.+/.+",
            r"Data/English/(?!generals\.csf$).+",
            r"Data/Audio/Sounds/rus-.+\.wav",
            r"Maps/[^/]+\.ini",
            r".+\.(txt|lnk)",
        ],
    )


MODS = [
    {
        "dest": "GO_Mac_Mod_Contra007",
        "assets": "Contra007",
        "catalog": {"id": "m_contra007", "shortName": "CONTRA 007", "theme": "contra"},
        "layers": [
            [
                Archive("Contra007", "!Contra007.big", "Contra007"),
                Archive("Contra007", "!Contra007-en.big", "Contra007-en"),
                Archive("Contra007", "!Contra006Music.big", "Contra006Music"),
                Archive(".", "!Contra-007-Fix.big", "Contra-007-Fix"),
            ],
            control_bar_pro_layer(),
        ],
        "extras": [
            ("Contra007/ariag.ttf", "ariag.ttf"),
            ("Contra007/Install_Final.bmp", "Install_Final.bmp"),
            ("Contra007/00000000.016", "00000000.016"),
            ("Contra007/00000000.256", "00000000.256"),
            ("Generals Zero Hour/Data/INI/GameData.ini", "Data/INI/GameData.ini"),
            ("Generals Zero Hour/Data/Scripts/SkirmishScripts.scb", "Data/Scripts/SkirmishScripts.scb"),
            ("Maps/MapCache.ini", "Maps/MapCache.ini"),
        ],
        "overrides": [
            ("Contra007", "Data\\English\\Art\\Textures\\TitleScreenuserinterface.tga",
             "overrides/TitleScreenuserinterface.tga"),
        ],
        "config": {
            "id": "contra007",
            "displayName": "Contra 007",
            "version": "0.07.1",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Curated Contra 007 (EN) + Fix + NetFix + Fixed AI scripts + MapFix cache",
            "author": "Contra Mod Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 300,
        },
    },
    {
        "dest": "GO_Mac_Mod_Contra008",
        "assets": "Contra008",
        "catalog": {"id": "m_contra008", "shortName": "CONTRA 008", "theme": "contra"},
        "layers": [
            [
                Archive("Contra008FINAL", "!Contra008.ctr", "Contra008"),
                Archive("Contra008FINAL", "!Contra008EN.ctr", "Contra008EN"),
                Archive("Contra008FINAL", "!Contra008VLoc.ctr", "Contra008VLoc"),
                Archive("Contra008FINAL", "!Contra008MNew.ctr", "Contra008MNew"),
            ],
            control_bar_pro_layer(),
        ],
        "extras": [
            ("Contra008FINAL/Install_Final_Contra.bmp", "Install_Final.bmp"),
        ],
        "overrides": [],
        "config": {
            "id": "contra008",
            "displayName": "Contra 008",
            "version": "8.0.0",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Curated Contra 008 Final (EN, localized VO, new music)",
            "author": "Contra Mod Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 970,
        },
    },
    {
        "dest": "GO_Mac_Mod_Contra009",
        "assets": "Contra009",
        "catalog": {"id": "m_contra009", "shortName": "CONTRA 009", "theme": "contra"},
        "layers": contra009_layers(),
        "extras": [
            ("Contra009Final/Install_Final_Contra.bmp", "Install_Final.bmp"),
            ("Contra009FinalPatch1/GenArial.ttf", "GenArial.ttf"),
        ],
        "overrides": [],
        "config": {
            "id": "contra009",
            "displayName": "Contra 009",
            "version": "9.0.0-hf4",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Curated Contra 009 Final + Patch1-3 + Hotfix3 (AI) + Hotfix4 (EN Leikeze, EngVO, new music)",
            "author": "Contra Mod Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 1800,
        },
    },
    {
        "dest": "GO_Mac_Mod_ContraX",
        "assets": "ContraX",
        "catalog": {"id": "m_contrax", "shortName": "CONTRA X", "theme": "contra"},
        "layers": contrax_layers(),
        "extras": [
            ("ContraXBeta2/GenArial.ttf", "GenArial.ttf"),
            ("ContraXBeta2/Install_Final_Contra.bmp", "Install_Final.bmp"),
        ],
        "overrides": [],
        "config": {
            "id": "contrax",
            "displayName": "Contra X",
            "version": "x-beta2-p1",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Curated Contra X Beta 2 + Patch 1 (EN, Enhanced music, Control Bar Pro)",
            "author": "Contra Mod Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 3200,
        },
    },
    {
        "dest": "GO_Mac_Mod_Apocalptic",
        "assets": "Apocalptic",
        "catalog": {"id": "m_apocalptic", "shortName": "APOCALPTIC", "theme": "contra"},
        "tree": Tree(
            "Apocalptic",
            skip_dirs=["MSS"],
            skip_suffixes=[".BAK"],
            rename={
                "340_ControlBarProZH.big": "00_ControlBarProZH.big",
                "340_ControlBarPro1080ZH.big": "01_ControlBarPro1080ZH.big",
                "340_ControlBarProData1080ZH.big": "02_ControlBarProData1080ZH.big",
                "340_ControlBarProArt1080ZH.big": "03_ControlBarProArt1080ZH.big",
            },
        ),
        "layers": [],
        "extras": [],
        "overrides": [],
        "anchors": [
            "00_ControlBarProZH.big",
            "03_ControlBarProArt1080ZH.big",
            "Install_Final.bmp",
            "Data/INI/Object/SupremeCommander.ini",
            "Data/INI/GameData.ini",
            "Art/W3D/12ABLT.W3D",
            "Maps/Ancient Chinese Land/Ancient Chinese Land.map",
        ],
        "config": {
            "id": "apocalptic",
            "displayName": "Apocalptic",
            "version": "unknown",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": False,
            "maskBaseScripts": True,
            "description": "Apocalptic Mod for Zero Hour, curated for macOS",
            "author": "Aloshka Tech Track / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 620,
        },
    },
    {
        "dest": "GO_Mac_Mod_Silent_Death",
        "assets": "Silent_Death",
        "catalog": {"id": "m_silent_death", "shortName": "SILENT DEATH", "theme": "contra"},
        "tree": Tree("Silent_Death"),
        "layers": [],
        "extras": [],
        "overrides": [],
        # One anchor per release part, so a part that never arrived reads as damaged.
        "anchors": [
            "Install_Final.bmp",
            "Data/INI/object/Turkey.ini",
            "00LSF0118.big",
            "Art/Textures/sdprchcm.dds",
            "Art/W3D/sddzr.w3d",
        ],
        "parts": [
            ["config.json", "Install_Final.bmp", "LSFkrInfEngineer.dds", "Data", "Maps", "Window"],
            ["!00EgyPatch.big", "00LSF0118.big", "Art/Terrain"],
            ["Art/Textures"],
            ["Art/W3D"],
        ],
        "config": {
            "id": "silent-death",
            "displayName": "Silent Death",
            "version": "25",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": False,
            "maskBaseScripts": True,
            "description": "Silent Death v25 for Zero Hour, curated for macOS",
            "author": "Silent Death Mod Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 5100,
        },
    },
    {
        "dest": "GO_Mac_Mod_ShockWave",
        "assets": "ShockWave",
        "catalog": {"id": "m_shockwave", "shortName": "SHOCKWAVE", "theme": "contra"},
        "layers": shockwave_layers(),
        "extras": [
            ("ShockWave_1.201/Install_Final_shw.bmp", "Install_Final.bmp"),
            ("ShockWave_1.201/Data/Movies/Comp_ArmourGen_000.bik", "Data/Movies/Comp_ArmourGen_000.bik"),
            ("ShockWave_1.201/Data/Movies/Comp_ArmourGen_inv_000.bik", "Data/Movies/Comp_ArmourGen_inv_000.bik"),
            ("ShockWave_1.201/Data/Movies/Comp_SalvageGen_000.bik", "Data/Movies/Comp_SalvageGen_000.bik"),
            ("ShockWave_1.201/Data/Movies/Comp_SalvageGen_inv_000.bik", "Data/Movies/Comp_SalvageGen_inv_000.bik"),
            ("ShockWave_1.201/Data/Movies/Comp_Shw_LaserGen_000.bik", "Data/Movies/Comp_Shw_LaserGen_000.bik"),
            ("ShockWave_1.201/Data/Movies/Comp_Shw_LaserGen_inv_000.bik", "Data/Movies/Comp_Shw_LaserGen_inv_000.bik"),
            ("ShockWave_1.201/Data/Movies/Comp_Shw_StealthGen_000.bik", "Data/Movies/Comp_Shw_StealthGen_000.bik"),
            ("ShockWave_1.201/Data/Movies/Comp_Shw_StealthGen_inv_000.bik", "Data/Movies/Comp_Shw_StealthGen_inv_000.bik"),
            ("ShockWave_1.201/Data/Movies/SW_GC_Background.bik", "Data/Movies/SW_GC_Background.bik"),
            ("ShockWave_1.201/Data/Movies/Shw_Intro.bik", "Data/Movies/Shw_Intro.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/China01_Final_00s.bik", "Data/Movies/China01_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/China02_Final_00s.bik", "Data/Movies/China02_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/China03_Final_00s.bik", "Data/Movies/China03_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/China04_Final_00s.bik", "Data/Movies/China04_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/China05_Final_00s.bik", "Data/Movies/China05_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/China06_Final_00s.bik", "Data/Movies/China06_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/China07_Final_00s.bik", "Data/Movies/China07_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA01_Final_00s.bik", "Data/Movies/GLA01_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA02_Final_00s.bik", "Data/Movies/GLA02_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA03_Final_00s.bik", "Data/Movies/GLA03_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA04_Final_00s.bik", "Data/Movies/GLA04_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA05_Final_00s.bik", "Data/Movies/GLA05_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA06_Final_00s.bik", "Data/Movies/GLA06_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA07_Final_00s.bik", "Data/Movies/GLA07_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/GLA08_Final_00s.bik", "Data/Movies/GLA08_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/USA01_Final_00s.bik", "Data/Movies/USA01_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/USA02_Final_00s.bik", "Data/Movies/USA02_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/USA03_Final_00s.bik", "Data/Movies/USA03_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/USA04_Final_00s.bik", "Data/Movies/USA04_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/USA06_Final_00s.bik", "Data/Movies/USA06_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/USA07_Final_00s.bik", "Data/Movies/USA07_Final_00s.bik"),
            ("Shockwave_Sinple_Player_Experience_2.1.3/Data/Movies/USA08_Final_00s.bik", "Data/Movies/USA08_Final_00s.bik"),
        ],
        "unpacked": [
            ("ShockWave_1.201/!Shw_ini.gib", "Data\\INI\\InGameUI.ini", "Data/INI/InGameUI.ini"),
        ],
        "overrides": [],
        "config": {
            "id": "shockwave",
            "displayName": "ShockWave",
            "version": "1.201-hf6-spe2.1.3",
            "packageVersion": 2,
            "baseGame": "zh",
            "online": False,
            "maskBaseScripts": True,
            "description": "ShockWave 1.201 + Hotfix v6 + Singleplayer Experience 2.1.3 (full campaigns, 12 challenges), curated for macOS",
            "author": "SWR Productions / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 1040,
        },
    },
    {
        "dest": "GO_Mac_Mod_RotR",
        "assets": "RotR",
        "catalog": {"id": "m_rotr", "shortName": "RISE OF THE REDS", "theme": "contra"},
        "layers": rotr_layers(),
        "extras": [
            ("ROTR_1.86/Install_Final_rotr.bmp", "Install_Final.bmp"),
            ("ROTR_1.85/00000000.016_", "00000000.016"),
            ("ROTR_1.85/00000000.256_", "00000000.256"),
            ("ROTR_1.85/Data/Movies/ROTR_Intro.bik", "Data/Movies/ROTR_Intro.bik"),
        ],
        "overrides": [],
        "config": {
            "id": "rotr",
            "displayName": "Rise of the Reds",
            "version": "1.86",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": False,
            "maskBaseScripts": True,
            "description": "Rise of the Reds 1.85 + Patch 1.86, curated for macOS",
            "author": "SWR Productions / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 1230,
        },
    },
    {
        "dest": "GO_Mac_Mod_Old_Boss_R3",
        "assets": "Old_Boss_R3",
        "catalog": {"id": "m_old_boss_r3", "shortName": "OLD BOSS R3", "theme": "contra"},
        "layers": [
            [
                Archive(".", "0Boss Generals.big", "BossGenerals"),
            ],
            control_bar_pro_zh_layer(),
        ],
        "extras": [
            ("Old_Boss_R3/Install_Final.bmp", "Install_Final.bmp"),
        ],
        "unpacked": [
            ("0Boss Generals.big", "Data\\INI\\InGameUI.ini", "Data/INI/InGameUI.ini"),
        ],
        "overrides": [],
        "config": {
            "id": "old-boss-r3",
            "displayName": "Old Boss R3",
            "version": "R3",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Boss Generals R3 (Boss, CTF and AoD modes) + Control Bar Pro 1.2, curated for macOS",
            "author": "MaD-X Game and Mod Design / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 425,
        },
    },
    {
        "dest": "GO_Mac_Mod_NProject",
        "assets": "NProject",
        "catalog": {"id": "m_nproject", "shortName": "NPROJECT", "theme": "contra"},
        "layers": [
            [
                Archive("n5p29-nprojectbeta-v211", "!npm_art.big", "Art"),
                Archive("n5p29-nprojectbeta-v211", "!npm_art2.big", "Art2"),
                Archive("n5p29-nprojectbeta-v211", "!npm_art3.big", "Art3"),
                Archive("n5p29-nprojectbeta-v211", "!npm_audio.big", "Audio"),
                Archive("n5p29-nprojectbeta-v211", "!npm_data.big", "Data"),
                Archive("n5p29-nprojectbeta-v211", "!npm_maps.big", "Maps"),
            ],
            control_bar_pro_zh_layer(),
        ],
        "extras": [
            ("n5p29-nprojectbeta-v211/Install_Final.bmp", "Install_Final.bmp"),
            ("n5p29-nprojectbeta-v211/00000000.016", "00000000.016"),
            ("n5p29-nprojectbeta-v211/00000000.256", "00000000.256"),
        ],
        "unpacked": [
            ("n5p29-nprojectbeta-v211/!npm_data.big", "Data\\INI\\InGameUI.ini", "Data/INI/InGameUI.ini"),
        ],
        "overrides": [],
        "config": {
            "id": "nproject",
            "displayName": "NProject",
            "version": "2.11",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "NProject 2.11 (bug fixes, rebalance, playable Boss General with AI) + Control Bar Pro 1.2, curated for macOS",
            "author": "n5p29 (Enlima29) / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 650,
        },
    },
    {
        "dest": "GO_Mac_Mod_ContraX_Brutal",
        "assets": "ContraX_Brutal",
        "catalog": {"id": "m_contrax_brutal", "shortName": "CONTRA X BRUTAL", "theme": "contra"},
        "layers": contrax_brutal_layers(),
        "extras": [
            (f"{CONTRAX_TREE}/GenArial.ttf", "GenArial.ttf"),
            (f"{CONTRAX_TREE}/Install_Final.bmp", "Install_Final.bmp"),
            ("ContraX_Brutal/!ReplacerPatch1Fix.ini", "Data/INI/Object/!ReplacerPatch1Fix.ini"),
            ("ContraX_Brutal/Generals.str", "Data/Generals.str"),
        ],
        "overrides": [],
        "parts": [
            ["config.json", "GenArial.ttf", "Install_Final.bmp", "Data",
             "00_BossReplacer.big", "01_CameosHD.big", "02_ControlBarPro.big", "04_Patch1.big",
             "13_Textures.big", "16_Window.big"],
            ["03_DisableFogEffects.big", "05_AI.big", "06_Audio.big", "07_GameData.big",
             "09_INI.big", "11_MusicEnhanced.big"],
            ["08_HotkeysOriginal_English.big", "10_Maps.big", "12_Terrain.big",
             "14_UnitVoicesEnglish.big", "15_W3D.big"],
        ],
        "config": {
            "id": "contrax-brutal",
            "displayName": "Contra X Brutal",
            "version": "x-beta2-p1-boss2.1.13-fix1",
            "packageVersion": 2,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Curated Contra X Beta 2 + Patch 1 + Boss Replacer 2.1.13 with the Patch 1 definitions it dropped restored (EN, Enhanced music, Control Bar Pro)",
            "author": "Contra Mod Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 2400,
        },
    },
    {
        "dest": "GO_Mac_Mod_TEOD",
        "assets": "TEOD",
        "catalog": {"id": "m_teod", "shortName": "THE END OF DAYS", "theme": "contra"},
        "layers": [
            [
                Archive("MODDB_Ver11", "!TEOD_English.big", "English"),
                Archive("MODDB_Ver11", "!TEOD_INI.big", "INI"),
                Archive("MODDB_Ver11", "!TEOD_Maps.big", "Maps"),
                Archive("MODDB_Ver11", "!TEOD_Music.big", "Music"),
                Archive("MODDB_Ver11", "!TEOD_Sounds.big", "Sounds"),
                Archive("MODDB_Ver11", "!TEOD_Speech.big", "Speech"),
                Archive("MODDB_Ver11", "!TEOD_Terrain.big", "Terrain"),
                Archive("MODDB_Ver11", "!TEOD_Textures.big", "Textures"),
                Archive("MODDB_Ver11", "!TEOD_Voices.big", "Voices"),
                Archive("MODDB_Ver11", "!TEOD_W3D.big", "W3D"),
                Archive("MODDB_Ver11", "!TEOD_Window.big", "Window"),
            ],
        ],
        "extras": [
            ("MODDB_Ver11/Install_Final.bmp", "Install_Final.bmp"),
            ("MODDB_Ver11/Data/English/generals.csf", "Data/English/generals.csf"),
            ("MODDB_Ver11/Data/Scripts/MultiplayerScripts.scb", "Data/Scripts/MultiplayerScripts.scb"),
            ("MODDB_Ver11/Data/Scripts/Scripts.ini", "Data/Scripts/Scripts.ini"),
            ("MODDB_Ver11/Data/Scripts/SkirmishScripts.scb", "Data/Scripts/SkirmishScripts.scb"),
        ] + [(f"MODDB_Ver11/Data/English/Movies/{movie}", f"Data/English/Movies/{movie}") for movie in TEOD_MOVIES],
        "overrides": [],
        "config": {
            "id": "teod",
            "displayName": "The End of Days",
            "version": "11",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "The End of Days Ver 11 (Russia faction, subfactions bought in-game), curated for macOS",
            "author": "The End of Days Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 1100,
        },
    },
    {
        "dest": "GO_Mac_Mod_OFS",
        "assets": "OFS",
        "catalog": {"id": "m_ofs", "shortName": "OPERATION FIRESTORM", "theme": "contra"},
        "layers": [
            [
                Archive("OFS_Beta02_EasyInstall", "!OFS_Art.big", "Art"),
                Archive("OFS_Beta02_EasyInstall", "!OFS_Audio.big", "Audio"),
                Archive("OFS_Beta02_EasyInstall", "!OFS_English.big", "English"),
                Archive("OFS_Beta02_EasyInstall", "!OFS_INI.big", "INI"),
                Archive("OFS_Beta02_EasyInstall", "!OFS_WindowWide.big", "WindowWide"),
            ],
            [
                Archive("OFS_Beta02_Patch01/OFS_Patch_0.2.1_ENGLISH", "!!OFS_PATCH.big", "Patch"),
            ],
            control_bar_pro_18_buttons_layer(),
            control_bar_hd_layer(),
        ],
        "extras": [
            ("OFS_Beta02_EasyInstall/Install_Final.bmp", "Install_Final.bmp"),
            ("OFS_Beta02_EasyInstall/Data/Scripts/MultiplayerScripts.scb", "Data/Scripts/MultiplayerScripts.scb"),
            ("OFS_Beta02_EasyInstall/Data/Scripts/Scripts.ini", "Data/Scripts/Scripts.ini"),
            ("OFS_Beta02_EasyInstall/Data/Scripts/SkirmishScripts.scb", "Data/Scripts/SkirmishScripts.scb"),
            ("OFS/AmericaTechGeneral.ini", "Data/INI/ControlBarScheme/AmericaTechGeneral.ini"),
            ("OFS/MainMenu.wnd", "Window/Menus/MainMenu.wnd"),
        ] + loose_files("OFS_Beta02_Mappack/OFS_Maps", "Maps"),
        "overrides": [],
        "config": {
            "id": "ofs",
            "displayName": "Operation Firestorm",
            "version": "0.2.1",
            "packageVersion": 2,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Operation: Firestorm Beta 02 + Patch 0.2.1 (EN) + map pack + Control Bar Pro 2.1.1 (18 buttons) + Control Bar HD, curated for macOS",
            "author": "Operation: Firestorm Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 400,
        },
    },
    {
        "dest": "GO_Mac_Mod_Blitz2",
        "assets": "Blitz2",
        "catalog": {"id": "m_blitz2", "shortName": "BLITZKRIEG II", "theme": "contra"},
        "layers": [
            [
                Archive("BlitzR3", "BlitzArt.Blitz", "Art"),
                Archive("BlitzR3", "BlitzAudio.Blitz", "Audio"),
                Archive("BlitzR3", "BlitzEnglish.blitz", "English"),
                Archive("BlitzR3", "BlitzGerman.blitz", "German"),
                Archive("BlitzR3", "BlitzINI.blitz", "INI"),
                Archive("BlitzR3", "BlitzMaps.blitz", "Maps"),
                Archive("BlitzR3", "BlitzMissions.Blitz", "Missions"),
                Archive("BlitzR3", "BlitzTerrain.Blitz", "Terrain"),
                Archive("BlitzR3", "BlitzWindow.Blitz", "Window"),
            ],
            [
                Archive("BlitzR3_301", "BlitzArt.Blitz", "Art"),
                Archive("BlitzR3_301", "BlitzEnglish.blitz", "English"),
                Archive("BlitzR3_301", "BlitzGerman.blitz", "German"),
                Archive("BlitzR3_301", "BlitzINI.blitz", "INI"),
                Archive("BlitzR3_301", "BlitzMaps.blitz", "Maps"),
            ],
        ],
        "extras": [
            ("BlitzR3/Install_Final.bmp", "Install_Final.bmp"),
        ] + loose_files("BlitzR3/Data/Movies", "Data/Movies"),
        "overrides": [],
        "config": {
            "id": "blitz2",
            "displayName": "Blitzkrieg II: The Finest Hour",
            "version": "3.01",
            "packageVersion": 1,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Blitzkrieg II: The Finest Hour R3 + official Patch 3.01 (EN, DE), curated for macOS",
            "author": "Derelict Studios / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 1100,
        },
    },
    {
        "dest": "GO_Mac_Mod_WW3",
        "assets": "WW3",
        "catalog": {"id": "m_ww3", "shortName": "WORLD WAR 3", "theme": "contra"},
        "layers": [
            [Archive("WW3_Mod", original, original[2:-4]) for original in WW3_ARCHIVES],
            control_bar_pro_zh_layer(),
        ],
        "overlay": ww3_overlay(),
        "extras": [
            ("WW3_Mod/Install_Final.bmp", "Install_Final.bmp"),
        ],
        "scheme_aliases": {
            "America8x6": ["Germany", "Japan", "SouthKorea", "Israel", "UK", "France"],
            "China8x6": ["Russia", "NorthKorea", "India"],
            "GLA8x6": ["Iraq", "Pakistan"],
        },
        "overrides": [],
        "parts": [
            ["config.json", "Install_Final.bmp", "00_ControlBarPro1080ZH.big",
             "01_ControlBarProArt1080ZH.big", "02_ControlBarProData1080ZH.big",
             "03_ControlBarProZH.big", "04_PMBeta993.big"],
            ["06_PMBeta995.big", "07_PMBeta996.big", "08_PMBeta997.big", "09_PMBeta998.big",
             "10_PMBeta999.big"],
            ["05_PMBeta994.big", "Art", "Data", "Maps", "Window"],
        ],
        "config": {
            "id": "ww3",
            "displayName": "World War 3 (Peace Mission Mod)",
            "version": "2024.05",
            "packageVersion": 2,
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "World War 3, a sub-mod of Peace Mission: 14 modern factions + Control Bar Pro 1.2, curated for macOS",
            "author": "nappyhairdo; Peace Mission by Lee Shin Fox / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 4600,
        },
    },
]


def resolve_layers(layers):
    """Later layers replace same-named archives, then ASCII order of originals decides priority."""
    merged = {}
    for layer in layers:
        for archive in layer:
            merged[archive.original] = archive

    return sorted(merged.values(), key=lambda archive: archive.rank)


def link(src, dest):
    if DRY_RUN:
        return

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        os.remove(dest)

    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


def big_entries(path):
    with open(path, "rb") as handle:
        count, _index = struct.unpack(">II", handle.read(16)[8:16])
        for _ in range(count):
            offset, size = struct.unpack(">II", handle.read(8))
            name = b""
            while True:
                char = handle.read(1)
                if char in (b"\x00", b""):
                    break
                name += char
            yield name.decode("latin-1"), offset, size


def apply_override(archive_path, entry_name, payload_path):
    """Replace one entry in place. Sizes must match, so the index stays valid."""
    payload = open(payload_path, "rb").read()

    for name, offset, size in big_entries(archive_path):
        if name != entry_name:
            continue

        if size != len(payload):
            raise SystemExit(
                f"override size mismatch for {entry_name}: archive {size}, asset {len(payload)}")

        with open(archive_path, "r+b") as handle:
            handle.seek(offset)
            handle.write(payload)
        return True

    raise SystemExit(f"override target not found in archive: {entry_name}")


def read_entry(archive_path, entry_name):
    for name, offset, size in big_entries(archive_path):
        if name.lower() != entry_name.lower():
            continue

        with open(archive_path, "rb") as handle:
            handle.seek(offset)
            return handle.read(size)

    raise SystemExit(f"entry not found in archive: {entry_name}")


def extract_entry(archive_path, entry_name, dest):
    payload = read_entry(archive_path, entry_name)

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as handle:
        handle.write(payload)


def write_scheme_aliases(aliases, dest):
    """Control Bar Pro ships schemes for the stock sides only, and a side without one falls
    back to "Default", which no mod defines. Every other side of the mod gets a copy of a stock
    scheme under its own name; the engine reads Data/INI/ControlBarScheme/ after the main file.
    """
    archive_path = os.path.join(SRC, CONTROL_BAR_PRO_ZH, "340_ControlBarProData1080ZH.big")
    text = read_entry(archive_path, "Data\\INI\\ControlBarScheme.ini").decode("latin-1").replace("\r\n", "\n")
    stock = {m.group(1): m.group(0) for m in re.finditer(r"(?ms)^ControlBarScheme\s+(\S+)\n.*?^End\s*$", text)}

    copies = []
    for scheme, sides in aliases.items():
        for side in sides:
            copy = re.sub(r"(?m)^ControlBarScheme\s+\S+", f"ControlBarScheme {side}8x6", stock[scheme], count=1)
            copy = re.sub(r"(?m)^(\s*Side\s*=?\s*)\S+", lambda m: m.group(1) + side, copy, count=1)
            copies.append(copy)

    if DRY_RUN:
        return len(copies)

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", newline="\r\n") as handle:
        handle.write("\n\n".join(copies) + "\n")

    return len(copies)


def missing_sources(mod):
    tree = mod.get("tree")
    if tree and not os.path.isdir(os.path.join(SRC, tree.source)):
        return f"downloads/files/{tree.source}/"

    overlay = mod.get("overlay")
    if overlay and not os.path.isdir(os.path.join(SRC, overlay.source)):
        return f"downloads/files/{overlay.source}/"

    for archive in resolve_layers(mod["layers"]):
        if not os.path.exists(archive.source):
            return f"{archive.layer_dir}/{archive.original}"

    for source, relative in mod["extras"]:
        override = os.path.join(ASSETS, mod["assets"], os.path.basename(relative))
        if not os.path.exists(override) and not os.path.exists(os.path.join(SRC, source)):
            return source

    for source, _entry_name, _relative in mod.get("unpacked", []):
        if not os.path.exists(os.path.join(SRC, source)):
            return source

    return None


def build(mod):
    dest_dir = os.path.join(ROOT, mod["dest"])
    asset_dir = os.path.join(ASSETS, mod["assets"])

    print(f"==> {mod['dest']}")

    # downloads/files is wiped whenever un_zip.sh runs for another mod, and a built tree
    # is the only copy left once its sources are gone. Rebuilding starts by deleting the
    # tree, so a missing source must stop us before that, not halfway through.
    missing = missing_sources(mod)
    if missing:
        print(f"    SKIPPED: source missing ({missing})", file=sys.stderr)
        return []

    if not DRY_RUN:
        shutil.rmtree(dest_dir, ignore_errors=True)
        os.makedirs(dest_dir, exist_ok=True)

    names = []
    tree = mod.get("tree")

    if tree:
        for source, relative in tree.files():
            names.append(relative)
            link(source, os.path.join(dest_dir, relative))
        print(f"    {len(names)} files <- downloads/files/{tree.source}/")

        # A layered mod names its local edits in "extras"; a tree has no such list, so
        # whatever sits in assets/<mod>/ simply wins over the file of the same name.
        for name in sorted(os.listdir(asset_dir) if os.path.isdir(asset_dir) else []):
            override = os.path.join(asset_dir, name)
            if not os.path.isfile(override):
                continue

            print(f"    {name:<34} <- assets/{mod['assets']}/{name}")
            link(override, os.path.join(dest_dir, name))
            if name not in names:
                names.append(name)

    for index, archive in enumerate(resolve_layers(mod["layers"])):
        filename = f"{index:02d}_{archive.name}.big"
        names.append(filename)
        print(f"    {filename:<34} <- {archive.layer_dir}/{archive.original}")
        link(archive.source, os.path.join(dest_dir, filename))

    overlay = mod.get("overlay")
    if overlay:
        loose = 0
        for source, relative in overlay.files():
            loose += 1
            link(source, os.path.join(dest_dir, relative))
        print(f"    {loose} loose files <- downloads/files/{overlay.source}/")

    for source, relative in mod["extras"]:
        override = os.path.join(asset_dir, os.path.basename(relative))
        if os.path.exists(override):
            print(f"    {relative:<34} <- assets/{mod['assets']}/{os.path.basename(relative)}")
            link(override, os.path.join(dest_dir, relative))
            continue

        print(f"    {relative:<34} <- {source}")
        link(os.path.join(SRC, source), os.path.join(dest_dir, relative))

    for source, entry_name, relative in mod.get("unpacked", []):
        print(f"    {relative:<34} <- {source} :: {entry_name}")
        if not DRY_RUN:
            extract_entry(os.path.join(SRC, source), entry_name, os.path.join(dest_dir, relative))

    scheme_aliases = mod.get("scheme_aliases")
    if scheme_aliases:
        relative = f"Data/INI/ControlBarScheme/{mod['assets']}Sides.ini"
        count = write_scheme_aliases(scheme_aliases, os.path.join(dest_dir, relative))
        print(f"    {relative:<34} <- {count} Control Bar Pro schemes for the mod's own sides")

    for archive_name, entry_name, asset_relative in mod["overrides"]:
        target = next(n for n in names if n.endswith(f"_{archive_name}.big"))
        payload = os.path.join(asset_dir, asset_relative)
        print(f"    patch {target} :: {entry_name}")

        if DRY_RUN:
            continue

        # Break the hardlink first: patching in place would corrupt downloads/.
        patched = os.path.join(dest_dir, target)
        temporary = patched + ".tmp"
        shutil.copy2(patched, temporary)
        os.replace(temporary, patched)
        apply_override(patched, entry_name, payload)

    if not DRY_RUN:
        with open(os.path.join(dest_dir, "config.json"), "w") as handle:
            json.dump(mod["config"], handle, indent=2)
            handle.write("\n")

    return names


def catalog_markers(mod):
    """Files the launcher checks to call a mod installed; it adds config.json itself."""
    # A loose mod holds thousands of files; the launcher checks a chosen few instead,
    # one per release part, which is what catches a part that never arrived.
    if mod.get("anchors"):
        return list(mod["anchors"])

    names = [f"{i:02d}_{a.name}.big" for i, a in enumerate(resolve_layers(mod["layers"]))]
    extras = [relative for _source, relative in mod["extras"]]
    unpacked = [relative for _source, _entry_name, relative in mod.get("unpacked", [])]

    return names + extras + unpacked


def release_zips(mod):
    """A mod ships as <dest>.zip, or as <dest>.1.zip, <dest>.2.zip ... once split."""
    single = f"{mod['dest']}.zip"
    if os.path.exists(os.path.join(ROOT, single)):
        return [single]

    parts = []
    while os.path.exists(os.path.join(ROOT, f"{mod['dest']}.{len(parts) + 1}.zip")):
        parts.append(f"{mod['dest']}.{len(parts) + 1}.zip")

    if not parts:
        raise SystemExit(f"no release zip for {mod['dest']}: run pack_upload.sh --no-upload first")

    return parts


def size_mb(paths):
    return round(sum(os.path.getsize(path) for path in paths) / 1024 ** 2)


def catalog_entry(mod):
    dest_dir = os.path.join(ROOT, mod["dest"])
    if not os.path.isdir(dest_dir):
        raise SystemExit(f"tree not built: {mod['dest']}")

    zips = release_zips(mod)
    config = mod["config"]
    tree_files = (os.path.join(current, name) for current, _dirs, names in os.walk(dest_dir) for name in names)

    return {
        "id": mod["catalog"]["id"],
        "baseGame": BASE_PROFILES[config["baseGame"]],
        "displayName": config["displayName"],
        "shortName": mod["catalog"]["shortName"],
        "theme": mod["catalog"]["theme"],
        "dirName": mod["dest"].removeprefix("GO_Mac_Mod_"),
        "packageVersion": config["packageVersion"],
        "urls": [f"{RELEASE_BASE}/{name}" for name in zips],
        "downloadSizeMB": size_mb(os.path.join(ROOT, name) for name in zips),
        "diskSizeMB": size_mb(tree_files),
        "markers": catalog_markers(mod),
        **publish_artwork(mod),
    }


def publish_artwork(mod):
    """assets/<mod>/banner.png and medallion.png go to the site under a content hash, so a new picture gets a new URL."""
    published = {}
    for kind in ARTWORK_KINDS:
        source = os.path.join(ASSETS, mod["dest"].removeprefix("GO_Mac_Mod_"), f"{kind}.png")
        if not os.path.isfile(source):
            continue

        with open(source, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()[:12]

        relative = f"mods/{mod['catalog']['id']}/{kind}-{digest}.png"
        destination = os.path.join(os.path.dirname(CATALOG), relative)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copyfile(source, destination)
        published[kind] = relative

    return published


def write_catalog():
    """public/api/mods.json of the site: the launcher's mod list, in switcher order."""
    if not os.path.isdir(os.path.dirname(CATALOG)):
        raise SystemExit(f"site repository not found: {os.path.dirname(CATALOG)}")

    shutil.rmtree(SITE_ARTWORK, ignore_errors=True)
    catalog = {"version": 1, "mods": [catalog_entry(mod) for mod in MODS]}
    with open(CATALOG, "w") as handle:
        json.dump(catalog, handle, indent=2)
        handle.write("\n")

    print(f"==> {os.path.relpath(CATALOG, ROOT)}: {len(MODS)} mods")


def write_contrax_parts(names):
    """pack_upload.sh sources these arrays; keep each release zip under 2 GiB."""
    dest_dir = os.path.join(ROOT, "GO_Mac_Mod_ContraX")
    limit = 2 * 1024 ** 3 - 64 * 1024 ** 2

    parts = [[], [], []]
    sizes = [0, 0, 0]

    fixed = ["config.json", "GenArial.ttf", "Install_Final.bmp"]
    parts[0].extend(fixed)

    for name in sorted(names, key=lambda n: -os.path.getsize(os.path.join(dest_dir, n))):
        index = min(range(3), key=lambda i: sizes[i])
        size = os.path.getsize(os.path.join(dest_dir, name))

        if sizes[index] + size > limit:
            raise SystemExit(f"cannot fit {name} into any release part")

        parts[index].append(name)
        sizes[index] += size

    lines = [
        "#!/bin/bash",
        "# Shared ContraX release-part file lists (relative to GO_Mac_Mod_ContraX/).",
        "# Generated by assemble_mods.py - do not edit by hand.",
        "# Rules: no overlap; config.json only in part 1; each zip stays under 2 GiB.",
        "",
    ]

    for number, part in enumerate(parts, start=1):
        lines.append(f"CONTRAX_PART{number}=(")
        lines.extend(f"  {entry}" for entry in sorted(part))
        lines.append(")")
        lines.append("")

    if not DRY_RUN:
        with open(os.path.join(ROOT, "contrax_parts.sh"), "w") as handle:
            handle.write("\n".join(lines))

    for number, size in enumerate(sizes, start=1):
        print(f"    part {number}: {size / 1024 ** 3:.2f} GiB")


def write_tree_parts(mod):
    """Emit the release-part lists of a loose mod: whole directories, not file lists.

    ContraX splits by archive because it has a dozen of them. A loose mod has
    thousands of files, so the parts are cut along top level directories and zip is
    handed those directly.
    """
    dest_dir = os.path.join(ROOT, mod["dest"])
    prefix = mod["config"]["id"].replace("-", "_").upper()
    lines = [
        "#!/bin/bash",
        f"# {mod['dest']} release-part lists (relative to {mod['dest']}/).",
        "# Generated by assemble_mods.py - do not edit by hand.",
        "# Rules: no overlap; config.json only in part 1; each zip stays under 2 GiB.",
        "",
    ]

    for number, entries in enumerate(mod["parts"], start=1):
        size = sum(
            os.path.getsize(os.path.join(current, name))
            for entry in entries
            for current, _dirs, names in os.walk(os.path.join(dest_dir, entry))
            for name in names
        ) + sum(
            os.path.getsize(os.path.join(dest_dir, entry))
            for entry in entries
            if os.path.isfile(os.path.join(dest_dir, entry))
        )

        print(f"    part {number}: {size / 1024 ** 3:.2f} GiB")
        lines.append(f"{prefix}_PART{number}=(")
        lines.extend(f'  "{entry}"' for entry in entries)
        lines.append(")")
        lines.append("")

    if not DRY_RUN:
        script = os.path.join(ROOT, f"{mod['config']['id'].replace('-', '_')}_parts.sh")
        with open(script, "w") as handle:
            handle.write("\n".join(lines))


def verify(mod):
    """Every .big must really be a BIG archive, and a mod is unusable without config.json."""
    dest_dir = os.path.join(ROOT, mod["dest"])
    failures = 0
    total = 0

    for current, _dirs, files in os.walk(dest_dir):
        for name in files:
            path = os.path.join(current, name)
            total += os.path.getsize(path)

            if not name.endswith(".big"):
                continue

            with open(path, "rb") as handle:
                if handle.read(4) != b"BIGF":
                    print(f"    WARN not BIGF: {name}", file=sys.stderr)
                    failures += 1

    if not os.path.exists(os.path.join(dest_dir, "config.json")):
        print(f"    WARN missing config.json in {mod['dest']}", file=sys.stderr)
        failures += 1

    print(f"--- {mod['dest']}: {total / 1024 ** 3:.2f} GiB, "
          f"{sum(len(f) for _r, _d, f in os.walk(dest_dir))} files"
          f"{'' if failures == 0 else f', {failures} PROBLEMS'}")

    return failures


def selected_mods():
    """No arguments means every mod; a name picks one, matching either id or folder."""
    if not TARGETS:
        return MODS

    chosen = []
    for target in TARGETS:
        wanted = target.lower().replace("-", "").replace("_", "")
        matches = [m for m in MODS
                   if wanted in (m["config"]["id"].replace("-", ""), m["dest"].lower().replace("go_mac_mod_", ""))]
        if not matches:
            raise SystemExit(f"unknown mod: {target} "
                             f"(known: {', '.join(m['config']['id'] for m in MODS)})")
        chosen.extend(matches)

    return chosen


def main():
    if EMIT_CATALOG:
        write_catalog()
        return

    if DRY_RUN:
        print("(dry run: nothing is written)\n")

    contrax_names = []
    mods = selected_mods()

    for mod in mods:
        names = build(mod)
        if mod["dest"] == "GO_Mac_Mod_ContraX":
            contrax_names = names
        print()

    if contrax_names and not DRY_RUN:
        print("==> ContraX release parts")
        write_contrax_parts(contrax_names)

    for mod in mods:
        if mod.get("parts"):
            print(f"==> {mod['dest']} release parts")
            write_tree_parts(mod)
            print()

    if DRY_RUN:
        print("\nDone.")
        return

    print("\n==> Summary")
    failures = sum(verify(mod) for mod in mods)

    if failures:
        raise SystemExit(f"\n{failures} problem(s) found.")

    print("\nDone.")


if __name__ == "__main__":
    main()
