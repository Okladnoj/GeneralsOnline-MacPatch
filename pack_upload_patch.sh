#!/bin/bash
set -e

# Change to the directory of the script
cd "$(dirname "$0")"

echo "📦 Packing GO_Mac_Patch folder into a ZIP archive..."
rm -f GO_Mac_Patch.zip
cd GO_Mac_Patch
zip -r ../GO_Mac_Patch.zip . -x "*.DS_Store"
cd ..

echo "📤 Uploading GO_Mac_Patch.zip to GitHub (release v1.0)..."
gh release upload v1.0 GO_Mac_Patch.zip --repo Okladnoj/GeneralsOnline-MacPatch --clobber

echo "✅ Done! Patch packed and uploaded to GitHub."
