#!/bin/sh

CHD=gdl-0018.chd
INFO=BFR.BIN
PAYLOAD=AZUPB.BIN
KEY=B5673138E69798A2
WORKDIR=unpacked

set -euo pipefail

SCRIPTDIR="$(dirname -- "$(realpath -- "$0")")"

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

# this particular game has lots of LZKJ'd textures, so do them here
IFS="
"

for bin in $(cd $WORKDIR/naomi; find * -name '*.BIN')
do
    binfile="$(realpath -- "$WORKDIR/naomi/$bin")"

    mkdir -p $WORKDIR/unlz/$bin
    pushd $WORKDIR/unlz/$bin > /dev/null

    "$SCRIPTDIR"/unLZKJ.py "$binfile"

    popd > /dev/null
done
