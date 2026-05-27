#!/bin/bash
set -e

# Change to the directory of the script
cd "$(dirname "$0")"

echo "📥 Downloading GO_Mac_Patch.zip from GitHub (release v1.0)..."
gh release download v1.0 -p "GO_Mac_Patch.zip" --repo Okladnoj/GeneralsOnline-MacPatch --clobber

echo "📦 Unpacking the archive..."
rm -rf GO_Mac_Patch
unzip -q GO_Mac_Patch.zip

echo "✅ Done! Patch unpacked to the GO_Mac_Patch folder."
