#!/usr/bin/env python3

import struct
import png  # pypi package: pypng
import sys

def twiddle(x, y):
    x = (x | (x << 8)) & 0x00FF00FF
    x = (x | (x << 4)) & 0x0F0F0F0F
    x = (x | (x << 2)) & 0x33333333
    x = (x | (x << 1)) & 0x55555555

    y = (y | (y << 8)) & 0x00FF00FF
    y = (y | (y << 4)) & 0x0F0F0F0F
    y = (y | (y << 2)) & 0x33333333
    y = (y | (y << 1)) & 0x55555555

    z = x | (y << 1)

    return z

if len(sys.argv) not in [2, 3]:
    print(f"usage: {sys.argv[0]} infile.pvr [outfile.png]")
    sys.exit(1)

if len(sys.argv) == 2:
    sys.argv.append(sys.argv[1][:-4] + '.png')

with open(sys.argv[1], 'rb') as fp:
    fp.seek(0x20)
    raw_bytes = fp.read()
    raw = struct.unpack(f'<{len(raw_bytes)//2}H', raw_bytes)

image = []
for row in range(512):
    image.append([0]*(3*512))

for x in range(512):
    for y in range(512):
        z = twiddle(y, x)

        if z < len(raw):
            rawval = raw[z]
            row = image[y]
            r = (rawval >> 11) << 3
            g = ((rawval >> 5) & 0x3f) << 2
            b = (rawval & 0x1f) << 3
            row[x*3] = r
            row[x*3 + 1] = g
            row[x*3 + 2] = b

png.from_array(image, 'RGB').save(sys.argv[2])
