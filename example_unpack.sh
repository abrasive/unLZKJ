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

mkdir -p "$WORKDIR"

# chdman needs to be on your PATH
chdman extractcd -i "$CHD" -o "$WORKDIR/disc.gdi" -f

./gdipack.py unpack "$WORKDIR/disc.gdi" "$WORKDIR/disc"

./naomipack.py unpack "$WORKDIR/disc/$PAYLOAD" "$WORKDIR/naomi" $KEY
