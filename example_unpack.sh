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

# get GAMEFILE (in azumanga this is AZUPB.BIN)
eval $(./bfriend.py dump "$WORKDIR/disc/$INFO")

./naomipack.py unpack "$WORKDIR/disc/$GAMEFILE" "$WORKDIR/naomi" $KEY

# azumanga in particular has lots of LZKJ'd textures, so unpack them here
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
