#!/usr/bin/env python3

import struct

def lz_init_tab():
    tab = []

    for r5 in range(0x10):
        r6 = r5
        r6 <<= 4
        r3 = r5
        r6 += r3

        for r4 in range(0x100):
            tab.append(r6 & 0xff)

    return tab

def lz_decompress(filename):
    with open(filename, 'rb') as fp:
        header = fp.read(0x1c)

        assert header[:4] == b'LZKJ'
        assert header[0xc:0xe] == b'LZ'   # 'CP' also supported by the game
        compressed_len, uncompressed_len, name_len = struct.unpack('<LLL', header[0x10:0x1c])
        name_align = (name_len+3) & ~3
        name = fp.read(name_align)[:name_len]
        print('decompressing:', name.decode('ascii'))

        data = fp.read(compressed_len)

    lz_tab = lz_init_tab()

    data = bytearray(data)
    def take16():
        first = data.pop(0)
        second = data.pop(0)
        return first + (second << 8)

    def take8():
        return data.pop(0)

    actions = 0
    num_actions = 0

    lz_index_w = 0
    out = bytearray()
    fo = open('test.bin', 'wb')

    while len(out) < uncompressed_len:
        actions >>= 1
        num_actions -= 1

        if num_actions <= 0:
            actions = take16()
            num_actions = 16

        if actions & 1: # do a literal
            literal = take8()

            lz_tab[lz_index_w] = literal
            lz_index_w = (lz_index_w + 1) & 0xfff

            out.append(literal)
            continue

        else:
            word = take16()
            lz_index_r = word & 0xfff
            todo = (word >> 12) + 2

            if todo == 0x11:
                todo = take8() + 0x11

                if todo == 0x110:
                    todo = take16() + 0x110

            if len(out) + todo > uncompressed_len:
                todo = uncompressed_len - len(out)

            for _ in range(todo):
                byte = lz_tab[lz_index_r]
                lz_index_r = (lz_index_r + 1) & 0xfff

                lz_tab[lz_index_w] = byte
                lz_index_w = (lz_index_w + 1) & 0xfff

                out.append(byte)

    return name, out

if __name__ == "__main__":
    import sys

    if len(sys.argv) not in [2, 3]:
        print(f"usage: {sys.argv[0]} infile.lz [outfile.pvr]")
        sys.exit(1)

    outfile, data = lz_decompress(sys.argv[1])

    if len(sys.argv) == 3:
        outfile = sys.argv[2]

    open(outfile, 'wb').write(data)
