#!/usr/bin/env python3
"""
Extract the disc info filename and the encryption key from a MAME-style
Naomi ROM (.zip or .pic)
"""

import pathlib
import sys
import zipfile

class DumpError(Exception):
    pass

def dump_pic(fp):
    data = fp.read(0x800)[0x600::2]

    key = data[0xc0:0xc7] + data[0xd0:0xd1]
    infofile = data[0xe0:0xe7].decode('ascii')

    print(f'KEY={key.hex()}')
    print(f'INFO={infofile}')

def dump_zip(fp):
    zf = zipfile.ZipFile(fp)
    names = zf.namelist()

    if len(names) != 1:
        raise DumpError('Expected one file in the zip, found %d' % len(names))

    if not names[0].lower().endswith('.pic'):
        raise DumpError('Expected a .pic file in the zip, found "%s"' % names[0])

    with zf.open(names[0], 'r') as picfp:
        dump_pic(picfp)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: %s rom.{zip,pic}" % sys.argv[0])
        sys.exit(1)

    file = pathlib.Path(sys.argv[1])
    fp = file.open('rb')

    try:
        if file.suffix.lower() == '.pic':
            dump_pic(fp)
        else:
            dump_zip(fp)

    except DumpError as e:
        print("ERROR:", *e.args)
