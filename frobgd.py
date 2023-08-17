#!/usr/bin/env python3

import pycdlib  # pypi: pycdlib
import des  # pypi: des
from io import BytesIO
import os
import sys
import pathlib

class RemapFp(object):
    "Remap sectors from a gd-rom fp so an ISO reader can handle it"
    def __init__(self, fp, file_offset=0):
        self.fp = fp
        self.file_offset = file_offset

        self.fp.seek(0, os.SEEK_END)
        self.file_size = self.fp.tell()

    def seek(self, offset, whence=0):
        if whence == os.SEEK_SET:
            self.offset = offset
        elif whence == os.SEEK_CUR:
            self.seek(self.offset + offset)
            return
        elif whence == os.SEEK_END:
            self.offset = self.file_size - self.file_offset + 45000*0x800
        else:
            raise NotImplementedError()

        if offset <= 0x9000: # leave the PVD where it is; pycdlib then expects to read a little more
            self.fp.seek(self.file_offset + offset)
        else:
            self.fp.seek(self.file_offset + offset - 45000*0x800)

    def tell(self):
        return self.offset

    def read(self, count):
        data = self.fp.read(count)
        self.offset += len(data)
        return data

    def write(self, data):
        n = self.fp.write(data)
        self.offset += n
        return n

class EncryptedFp(object):
    "Apply en/decryption while reading/writing a file at some offset"
    def __init__(self, fp, key_ascii, offset=0):
        self.fp = fp
        self.des = des.DesKey(bytes.fromhex(key_ascii)[::-1])
        self.file_offset = offset
        self.fp.seek(offset)

        raise NotImplementedError() # XXX


def unpack(iso, rootdir: pathlib.Path, iso_path=''):
    for child in iso.list_children(iso_path=iso_path + '/'):
        filename = child.file_identifier().decode('ascii')
        print(iso_path + '/' + filename)

        if child.is_dir() and filename not in ['', '.', '..']:
            (rootdir / filename).mkdir(exist_ok=True)
            unpack(iso, rootdir / filename, iso_path + '/' + filename)

        elif child.is_file():
            with (rootdir / filename[:-2]).open('wb') as fp:
                iso.get_file_from_iso_fp(fp, iso_path=iso_path + '/' + filename)

def repack(iso, rootdir: pathlib.Path, iso_path=''):
    for child in iso.list_children(iso_path=iso_path + '/'):
        filename = child.file_identifier().decode('ascii')

        if child.is_dir() and filename not in ['', '.', '..']:
            repack(iso, rootdir / filename, iso_path + '/' + filename)

        elif child.is_file():
            realfile = rootdir / filename[:-2]
            if not realfile.is_file():
                continue

            isop = iso_path + '/' + filename
            original = BytesIO()
            iso.get_file_from_iso_fp(original, iso_path=isop)

            if realfile.read_bytes() == original.getvalue():
                continue

            with realfile.open('rb') as fp:
                fp.seek(0, os.SEEK_END)
                size = fp.tell()
                fp.seek(0)
                iso.modify_file_in_place(fp, size, isop)

            print('Updated', iso_path + '/' + filename[:-2])

if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ["unpack", "repack"]:
        print(f"usage: {sys.argv[0]} [unpack|repack] file.iso rootdir")
        sys.exit(1)

    if sys.argv[1] == 'unpack':
        op = unpack
        mode = 'rb'
    else:
        op = repack
        mode = 'r+b'

    realfp = open(sys.argv[2], mode)
    fakefp = RemapFp(realfp, 0x800000)

    iso = pycdlib.PyCdlib()
    iso.open_fp(fakefp)

    rootdir = pathlib.Path(sys.argv[3])
    rootdir.mkdir(exist_ok=True)

    op(iso, rootdir)
