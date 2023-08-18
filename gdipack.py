#!/usr/bin/env python3

import frobgd
import sys
import pycdlib
import pathlib

def find_data_track(gdi_file: pathlib.Path):
    contents = gdi_file.read_text()
    lines = [line.strip() for line in contents.split('\n') if line.strip() != '']
    ntracks = int(lines[0])
    # I only know how to interpret the last data track
    s_tno, s_lba, s_mode, s_secsz, filename, s_offset = lines[-1].split()
    tno = int(s_tno)
    lba = int(s_lba)
    mode = int(s_mode)
    secsz = int(s_secsz)
    offset = int(s_offset)

    return {
            'file': gdi_file.parent / filename,
            'sector_size': secsz,
            'offset': offset,
            }


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ["unpack", "repack"]:
        print(f"usage: {sys.argv[0]} [unpack|repack] file.gdi rootdir")
        sys.exit(1)

    if sys.argv[1] == 'unpack':
        op = frobgd.unpack
        mode = 'rb'
    else:
        op = frobgd.repack
        mode = 'r+b'

    data_track = find_data_track(pathlib.Path(sys.argv[2]))

    fp = data_track['file'].open(mode)

    if data_track['sector_size'] == 2048:
        remap_offset = data_track['offset']
    elif data_track['sector_size'] == 2352:
        fp = frobgd.SectorSizeFilter(fp)
        remap_offset = data_track['offset'] * 2048 // 2352
    else:
        print("ERROR: unsupported sector size")
        sys.exit(1)

    isofp = frobgd.RemapFilter(fp, remap_offset)

    iso = pycdlib.PyCdlib()
    iso.open_fp(isofp)

    rootdir = pathlib.Path(sys.argv[3])
    rootdir.mkdir(exist_ok=True)

    op(iso, rootdir)
