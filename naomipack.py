#!/usr/bin/env python3

import frobgd
import sys
import pycdlib
import pathlib

if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] not in ["unpack", "repack"]:
        print(f"usage: {sys.argv[0]} [unpack|repack] file.bin rootdir key")
        sys.exit(1)

    if sys.argv[1] == 'unpack':
        op = frobgd.unpack
        mode = 'rb'
    else:
        op = frobgd.repack
        mode = 'r+b'

    try:
        key = bytes.fromhex(sys.argv[4])
        if len(key) != 8:
            raise ValueError()
    except ValueError:
        print("ERROR: key must be 8 bytes / 16 hex digits")
        sys.exit(1)

    realfp = open(sys.argv[2], mode)
    clearfp = frobgd.CryptFilter(realfp, key)

    if clearfp.read(8) != b'NAOMI   ':
        print("\n*** WARNING: encryption key doesn't seem right? Attempting to continue...\n")

    isofp = frobgd.RemapFilter(clearfp, 0x800000)

    iso = pycdlib.PyCdlib()
    iso.open_fp(isofp)

    rootdir = pathlib.Path(sys.argv[3])
    rootdir.mkdir(exist_ok=True)

    op(iso, rootdir)
