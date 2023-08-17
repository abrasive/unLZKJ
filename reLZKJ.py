#!/usr/bin/env python3

import itertools
import struct
import tqdm     # pypi: tqdm
import pathlib

def find_all_chars(string, value):
    next_start = 0
    if len(value) > 1:
        string = string + string[:len(value) - 1]
    while (found := string.find(value, next_start)) >= 0:
        next_start = found + 1
        yield found

def lz_compress(queue):
    window = []
    for base in range(0x10):
        window += [base*0x11] * 0x100
    window = bytearray(window)

    ops = []

    t = tqdm.tqdm(total=len(queue), unit='byte', unit_scale=1, unit_divisor=1024, leave=False)
    bytes_done = 0
    while len(queue):
        best_match_start = None
        best_match_len = 1   # don't make backrefs that are longer than literals

        for match_start in find_all_chars(window, queue[:2]):
            backref = itertools.cycle(window[match_start:])
            match_len = 0
            while (match_len < len(queue)
                   and match_len < 0x110 + 0xffff
                   and queue[match_len] == next(backref)):
                match_len += 1

            if match_len > best_match_len:
                best_match_start = match_start
                best_match_len = match_len

        if best_match_start is not None:
            ops.append((best_match_start, best_match_len))
            advance = best_match_len
        else:
            ops.append(queue[0])
            advance = 1

        window = window[advance:] + queue[:advance]
        window = window[-4096:]
        queue = queue[advance:]
        t.update(advance)

    return ops

def lz_pack_ops(ops):
    packed = bytearray()
    bytes_done = 0

    for start in range(0, len(ops), 16):
        block_ops = ops[start:start+16]

        control_word = 0
        bit = 1
        for op in block_ops:
            if isinstance(op, int):
                control_word |= bit
            bit <<= 1

        packed.extend(struct.pack('<H', control_word))

        for op in block_ops:
            if isinstance(op, int):
                packed.append(op)
                bytes_done += 1
            else:
                start, length = op
                # we calculated start relative to a sliding window, but the format uses a wrapping one
                wrap_start = (start + bytes_done) & 0xfff

                if length >= 0x110:
                    packed.extend(struct.pack('<HBH', 0xf000 | wrap_start, 0xff, length - 0x110))
                elif length >= 0x11:
                    packed.extend(struct.pack('<HB',  0xf000 | wrap_start, length - 0x11))
                else:
                    packed.extend(struct.pack('<H',   (length-2)<<12 | wrap_start))
                bytes_done += length

    return packed

def compress_file(src_file: pathlib.Path):
    src_data = src_file.read_bytes()

    ops = lz_compress(src_data)
    compressed = lz_pack_ops(ops)

    header = b'LZKJ0.01\0\0\0\0LZ\0\0'
    header += struct.pack('<LLL', len(compressed), len(src_data), len(src_file.name))
    header += src_file.name.encode('ascii') + b'\0'
    while len(header) & 3:
        header += b'\0'

    return header + compressed

def compress_archive(dst_file: pathlib.Path, src_files: list[pathlib.Path]):
    compressed = [compress_file(file) for file in tqdm.tqdm(src_files, unit='file')]
    offsets = [4*len(compressed)]
    for data in compressed[:-1]:
        offsets.append(offsets[-1] + len(data))

    with dst_file.open('wb') as fp:
        for offset in offsets:
            fp.write(struct.pack('<L', offset))

        for data in compressed:
            fp.write(data)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} outfile.bin infile.pvr [infile2.pvr [infile3.pvr...")
        sys.exit(1)

    dst_file = pathlib.Path(sys.argv[1])
    src_files = [pathlib.Path(f) for f in sys.argv[2:]]

    bad = 0
    for f in src_files:
        if not f.is_file():
            print(f"ERROR: file {f} not found")
            bad = 1
    if bad:
        sys.exit(1)

    compress_archive(dst_file, src_files)
