#!/usr/bin/env python3

import numpy as np
import png
import sys

B = [0x55555555, 0x33333333, 0x0F0F0F0F, 0x00FF00FF]
S = [1, 2, 4, 8]
def twiddle(x, y):
    x = (x | (x << S[3])) & B[3]
    x = (x | (x << S[2])) & B[2]
    x = (x | (x << S[1])) & B[1]
    x = (x | (x << S[0])) & B[0]

    y = (y | (y << S[3])) & B[3]
    y = (y | (y << S[2])) & B[2]
    y = (y | (y << S[1])) & B[1]
    y = (y | (y << S[0])) & B[0]

    z = x | (y << 1)

    return z

if len(sys.argv) != 3:
    print(f"usage: {sys.argv[0]} infile.pvr outfile.png")
    sys.exit(1)

raw = np.fromfile(sys.argv[1], np.uint16, offset=0x20)
pixels = np.zeros((512,512), np.uint16)

for x in range(512):
    for y in range(512):
        z = twiddle(y, x)

        if z < len(raw):
            pixels[x, y] = raw[z]

pngvals = []
for y in range(512):
    row = []
    pngvals.append(row)
    for x in range(512):
        raw = pixels[x, y]
        r = (raw >> 11) << 3
        g = ((raw >> 5) & 0x3f) << 2
        b = (raw & 0x1f) << 3
        row.extend([r, g, b])

png.from_array(pngvals, 'RGB').save(sys.argv[2])
