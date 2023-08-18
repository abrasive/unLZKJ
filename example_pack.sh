#!/bin/sh

CHD=gdl-0018.chd
INFO=BFR.BIN
PAYLOAD=AZUPB.BIN
KEY=B5673138E69798A2
WORKDIR=unpacked

set -euo pipefail

if [ ! -d venv ]; then
    virtualenv venv
    venv/bin/pip install -r requirements.txt
fi

. venv/bin/activate

echo Repacking $PAYLOAD...
./naomipack.py repack "$WORKDIR/disc/$PAYLOAD" "$WORKDIR/naomi" $KEY

./bfriend.py "$WORKDIR/disc/$INFO"

echo Repacking disc.gdi...
./gdipack.py repack "$WORKDIR/disc.gdi" "$WORKDIR/disc"

# chdman needs to be on your PATH
chdman createcd -i "$WORKDIR/disc.gdi" -o "patched-$CHD" -f

