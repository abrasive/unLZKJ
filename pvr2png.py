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
    header = fp.read(0x20)
    assert header[:4] == b'GBIX'
    # not implemented: actual global index contents
    assert header[0x10:0x14] == b'PVRT'  # perverts only

    pixfmt = header[0x18]
    dtype = header[0x19]

    assert pixfmt in [0, 1, 2] # ARGB1555, RGB565, ARGB4444
    assert dtype in [1, 0xd] # square twiddled, rectangular twiddled

    width, height  = struct.unpack('<HH', header[0x1c:0x20])

    fp.seek(0x20)
    raw_bytes = fp.read()
    raw = struct.unpack(f'<{len(raw_bytes)//2}H', raw_bytes)

if pixfmt == 0:
    colour_entries = 4
    png_format = 'RGBA'
    def unpack(row, x, packed):
        row[x*4] = int(round(((packed >> 10) & 0x1f) / 0x1f * 255))
        row[x*4 + 1] = int(round(((packed >> 5) & 0x1f) / 0x1f * 255))
        row[x*4 + 2] = int(round((packed & 0x1f) / 0x1f * 255))
        row[x*4 + 3] = int(round((packed >> 15) * 255))

elif pixfmt == 1:
    colour_entries = 3
    png_format = 'RGB'
    def unpack(row, x, packed):
        row[x*3] = int(round((packed >> 11) / 0x1f * 255))
        row[x*3 + 1] = int(round(((packed >> 5) & 0x3f) / 0x3f * 255))
        row[x*3 + 2] = int(round((packed & 0x1f) / 0x1f * 255))

elif pixfmt == 2:
    colour_entries = 4
    png_format = 'RGBA'
    def unpack(row, x, packed):
        row[x*4] = int(round(((packed >> 8) & 0xf) / 0xf * 255))
        row[x*4 + 1] = int(round(((packed >> 4) & 0xf) / 0xf * 255))
        row[x*4 + 2] = int(round((packed & 0xf) / 0xf * 255))
        row[x*4 + 3] = int(round((packed >> 12) / 0xf * 255))

else:
    raise ValueError(f"unsupported pixel format {pixfmt}")

image = []
for row in range(height):
    image.append([0]*(colour_entries*width))

stride = min(width, height)

block_offset = 0
for x0 in range(0, width, stride):
    for y0 in range(0, height, stride):
        for x in range(stride):
            for y in range(stride):
                z = twiddle(y, x) + block_offset

                if z < len(raw):
                    rawval = raw[z]
                    row = image[y0+y]
                    unpack(row, x0+x, rawval)

        block_offset += stride*stride

png.from_array(image, png_format).save(sys.argv[2])
