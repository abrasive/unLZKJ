#!/usr/bin/env python3

from Crypto.Cipher import DES # pypi: pycryptodome
import tqdm # pypi: tqdm
import sys
import os

if len(sys.argv) != 5 or sys.argv[1] not in "ed":
    print(f"usage: {sys.argv[0]} [e|d] infile outfile hex_key")
    sys.exit(1)

try:
    keybytes = bytes.fromhex(sys.argv[4])
    if len(keybytes) != 8:
        raise ValueError()
except ValueError:
    print("error: key must be 16 chars of hex")
    sys.exit(1)

key = DES.new(keybytes[::-1], DES.MODE_ECB)
if sys.argv[1] == 'd':
    op = key.decrypt
else:
    op = key.encrypt

with open(sys.argv[2], 'rb') as infp, open(sys.argv[3], 'wb') as outfp:
    infp.seek(0, os.SEEK_END)
    insize = infp.tell()
    infp.seek(0)

    t = tqdm.tqdm(total=insize, unit='byte', unit_scale=1, unit_divisor=1024)
    while idata := infp.read(8):
        odata = op(idata[::-1])[::-1]
        outfp.write(odata)
        t.update(8)
