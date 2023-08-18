#!/bin/sh

CHD=gdl-0018.chd
INFO=BFR.BIN
PAYLOAD=AZUPB.BIN
KEY=B5673138E69798A2
WORKDIR=unpacked
REPACK_LZ=0 # it's very slow, you probably don't want to do this automatically

set -euo pipefail

if [ ! -d venv ]; then
    virtualenv venv
    venv/bin/pip install -r requirements.txt
fi

. venv/bin/activate

IFS="
"
if [ "$REPACK_LZ" != "0" ]
then
    for bin in $(cd $WORKDIR/unlz; find * -type d -name '*.BIN')
    do
        binfile="$(realpath -- "$WORKDIR/naomi/$bin")"

        pushd $WORKDIR/unlz/$bin > /dev/null

        echo "Packing $binfile..."
        "$SCRIPTDIR"/reLZKJ.py "$binfile" *

        popd > /dev/null
    done
fi

echo Repacking $PAYLOAD...
./naomipack.py repack "$WORKDIR/disc/$PAYLOAD" "$WORKDIR/naomi" $KEY

./bfriend.py "$WORKDIR/disc/$INFO"

echo Repacking disc.gdi...
./gdipack.py repack "$WORKDIR/disc.gdi" "$WORKDIR/disc"

# chdman needs to be on your PATH
chdman createcd -i "$WORKDIR/disc.gdi" -o "patched-$CHD" -f

