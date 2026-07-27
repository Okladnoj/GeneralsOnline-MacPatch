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


class Archive:
    def __init__(self, layer_dir, original, name):
        self.layer_dir = layer_dir
        self.original = original
        self.name = name

    @property
    def source(self):
        return os.path.join(SRC, self.layer_dir, self.original)


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


def build(mod):
    dest_dir = os.path.join(ROOT, mod["dest"])
    asset_dir = os.path.join(ASSETS, mod["assets"])

    if EMIT_MARKERS:
        return emit_markers(mod)

    print(f"==> {mod['dest']}")

    if not DRY_RUN:
        shutil.rmtree(dest_dir, ignore_errors=True)
        os.makedirs(dest_dir, exist_ok=True)

    archives = resolve_layers(mod["layers"])
    names = []

    for index, archive in enumerate(archives):
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


def main():
    if DRY_RUN:
        print("(dry run: nothing is written)\n")

    contrax_names = []

    for mod in MODS:
        names = build(mod)
        if mod["dest"] == "GO_Mac_Mod_ContraX":
            contrax_names = names
        print()

    print("==> ContraX release parts")
    if contrax_names and not DRY_RUN:
        write_contrax_parts(contrax_names)

    if DRY_RUN:
        print("\nDone.")
        return

    print("\n==> Summary")
    failures = sum(verify(mod) for mod in MODS)

    if failures:
        raise SystemExit(f"\n{failures} problem(s) found.")

    print("\nDone.")


if __name__ == "__main__":
    main()
