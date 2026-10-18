#!/bin/bash
# Zips the data pack into build/craftablerooteddirt-<version>.zip; the version is the top section of CHANGELOG.md.
set -e
cd "$(dirname "$0")/.."
version=$(grep -m1 '^## ' CHANGELOG.md | cut -c4-)
mkdir -p build
out=build/craftablerooteddirt-$version.zip
rm -f "$out"
zip -qrX "$out" pack.mcmeta pack.png LICENSE data
echo "$out"
