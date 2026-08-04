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

import json
import os
import shutil
import struct
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "downloads", "files")
ASSETS = os.path.join(ROOT, "assets")

DRY_RUN = "--dry-run" in sys.argv or "--markers" in sys.argv
EMIT_MARKERS = "--markers" in sys.argv
TARGETS = [a for a in sys.argv[1:] if not a.startswith("-")]


class Archive:
    def __init__(self, layer_dir, original, name):
        self.layer_dir = layer_dir
        self.original = original
        self.name = name

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


# Unofficial Control Bar Pro 2.1.1 rebuilt for Contra by Hojjat. Nine leading '!' put it
# ahead of every patch, which is what lets it replace the mod's own control bar layout.
def control_bar_pro_layer():
    return [
        Archive("ControlBarPro_Contra_v2_1_1",
                "!!!!!!!!!ControlBarPro_Contra.big", "ControlBarPro_Contra"),
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


MODS = [
    {
        "dest": "GO_Mac_Mod_Contra007",
        "assets": "Contra007",
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
        "dest": "GO_Mac_Mod_Apocalptic",
        "assets": "Apocalptic",
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
        "dest": "GO_Mac_Mod_ContraX",
        "assets": "ContraX",
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
            "baseGame": "zh",
            "online": True,
            "maskBaseScripts": True,
            "description": "Curated Contra X Beta 2 + Patch 1 (EN, Enhanced music, Control Bar Pro)",
            "author": "Contra Mod Team / curated for macOS",
            "bigGlob": "*.big",
            "approxSizeMB": 3200,
        },
    },
]


def resolve_layers(layers):
    """Later layers replace same-named archives, then ASCII order of originals decides priority."""
    merged = {}
    for layer in layers:
        for archive in layer:
            merged[archive.original] = archive

    return [merged[key] for key in sorted(merged)]


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


def missing_sources(mod):
    tree = mod.get("tree")
    if tree and not os.path.isdir(os.path.join(SRC, tree.source)):
        return f"downloads/files/{tree.source}/"

    for archive in resolve_layers(mod["layers"]):
        if not os.path.exists(archive.source):
            return f"{archive.layer_dir}/{archive.original}"

    for source, relative in mod["extras"]:
        override = os.path.join(ASSETS, mod["assets"], os.path.basename(relative))
        if not os.path.exists(override) and not os.path.exists(os.path.join(SRC, source)):
            return source

    return None


def build(mod):
    dest_dir = os.path.join(ROOT, mod["dest"])
    asset_dir = os.path.join(ASSETS, mod["assets"])

    if EMIT_MARKERS:
        return emit_markers(mod)

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

    for source, relative in mod["extras"]:
        override = os.path.join(asset_dir, os.path.basename(relative))
        if os.path.exists(override):
            print(f"    {relative:<34} <- assets/{mod['assets']}/{os.path.basename(relative)}")
            link(override, os.path.join(dest_dir, relative))
            continue

        print(f"    {relative:<34} <- {source}")
        link(os.path.join(SRC, source), os.path.join(dest_dir, relative))

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


def emit_markers(mod):
    """Print the ModSpec.markers array for Launcher/Sources/GameProfile.swift."""
    # A loose mod holds thousands of files; the launcher checks a chosen few instead,
    # one per release part, which is what catches a part that never arrived.
    if mod.get("anchors"):
        print(f"        // {mod['dest']} - generated by assemble_mods.py --markers")
        print("        markers: [")
        for entry in mod["anchors"]:
            print(f'            "{entry}",')
        print("        ]")
        print()
        return []

    names = [f"{i:02d}_{a.name}.big" for i, a in enumerate(resolve_layers(mod["layers"]))]
    extras = [relative for _source, relative in mod["extras"]]

    print(f"        // {mod['dest']} - generated by assemble_mods.py --markers")
    print("        markers: [")
    for entry in names + extras:
        print(f'            "{entry}",')
    print("        ]")
    print()

    return names


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
