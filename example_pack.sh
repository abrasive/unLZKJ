#!/bin/sh

# Example for how to use the unpacking tools.
# Expects a MAME-style source with ROM in gamename.zip and CHD in
# gamename/gdl-xxxx.chd.  If you already know the encryption key and info
# filename you can skip the zip and set KEY=, INFO= and CHD= yourself.

# Azumanga Daioh Puzzle Bobble is our example
GAME=azumanga
WORKDIR=unpacked

# get INFO and KEY
eval $(./dump_naomi_rom.py $GAME.zip)
CHD=$(ls $GAME/)

REPACK_LZ=0 # azumanga specific - repack the .pvr files into .bin files? it's very slow, you probably don't want to do this automatically

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

# get GAMEFILE
eval $(./bfriend.py dump "$WORKDIR/disc/$INFO")

echo Repacking $GAMEFILE...
./naomipack.py repack "$WORKDIR/disc/$GAMEFILE" "$WORKDIR/naomi" $KEY

./bfriend.py update "$WORKDIR/disc/$INFO"

echo Repacking disc.gdi...
./gdipack.py repack "$WORKDIR/disc.gdi" "$WORKDIR/disc"

# chdman needs to be on your PATH
chdman createcd -i "$WORKDIR/disc.gdi" -o "azumanga/$CHD" -f
