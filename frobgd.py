#!/usr/bin/env python3

import pycdlib  # pypi: pycdlib
from Crypto.Cipher import DES  # pypi: pycryptodome
from io import BytesIO
import os
import sys
import pathlib

class RemapFilter(object):
    "Remap sectors from a gd-rom fp so an ISO reader can handle it"
    def __init__(self, fp, file_offset=0):
        self.fp = fp
        self.file_offset = file_offset

        self.fp.seek(0, os.SEEK_END)
        self.file_size = self.fp.tell()
        self.seek(0)

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

class CryptFilter(object):
    "Apply en/decryption while reading/writing a file"
    def __init__(self, fp, key_bytes: bytes):
        self.fp = fp
        assert len(key_bytes) == 8
        self.des = DES.new(key_bytes[::-1], DES.MODE_ECB)

    def seek(self, offset, whence=0):
        if offset & 7:
            raise NotImplementedError()
        self.fp.seek(offset, whence)

    def tell(self):
        return self.fp.tell()

    def read(self, count):
        out = b''
        for _ in range((count + 7) // 8):
            out += self.des.decrypt(self.fp.read(8)[::-1])[::-1]
        out = out[:count]
        assert len(out) == count
        return out

    def write(self, data):
        if self.tell() & 7:
            raise NotImplementedError()

        while len(data) & 7:
            data += b'\0'

        ndone = len(data)

        while len(data):
            encrypted = self.des.encrypt(data[:8][::-1])[::-1]
            self.fp.write(encrypted)
            data = data[8:]

        return ndone

class SectorSizeFilter(object):
    "Read/write a file with 2352-byte sectors. Does not update EDC/ECC data."
    def __init__(self, fp, file_offset=0):
        self.fp = fp
        self.file_offset = file_offset
        self.seek(0)

    def seek(self, offset, whence=0):
        sector = offset // 2048
        inside = offset % 2048

        if whence == os.SEEK_SET:
            real_offset = sector * 2352 + 16 + inside
            self.fp.seek(real_offset + self.file_offset)
            assert self.tell() == offset

        elif whence == os.SEEK_CUR:
            if inside != 0:
                raise NotImplementedError()
            self.fp.seek(sector * 2352, os.SEEK_CUR)
            return

        elif whence == os.SEEK_END:
            if offset != 0:
                raise NotImplementedError()
            self.fp.seek(offset, os.SEEK_END)

        else:
            raise NotImplementedError()

    def tell(self):
        real_offset = self.fp.tell() - self.file_offset
        sector = real_offset // 2352
        inside = (real_offset % 2352) - 16
        return sector * 2048 + inside

    def read(self, count):
        out = b''
        sector_remain = 2048 - (self.tell() % 2048)
        read = min(count, sector_remain)
        out += self.fp.read(read)
        self.fp.seek(2352 - 2048, os.SEEK_CUR)
        count -= read

        while count:
            read = min(count, 2048)
            out += self.fp.read(read)
            self.fp.seek(2352 - 2048, os.SEEK_CUR)
            count -= read

        return out

    def write(self, data):
        ndone = len(data)

        sector_remain = 2048 - (self.tell() % 2048)
        write = min(len(data), sector_remain)
        done = self.fp.write(data[:write])
        self.fp.seek(2352 - 2048, os.SEEK_CUR)
        data = data[done:]

        while len(data):
            write = min(len(data), 2048)
            done = self.fp.write(data[:write])
            self.fp.seek(2352 - 2048, os.SEEK_CUR)
            data = data[done:]

        return ndone

def unpack(iso, rootdir: pathlib.Path, iso_path=''):
    for child in iso.list_children(iso_path=iso_path + '/'):
        filename = child.file_identifier().decode('ascii')
        if child.is_dir() and filename not in ['', '.', '..']:
            (rootdir / filename).mkdir(exist_ok=True)
            unpack(iso, rootdir / filename, iso_path + '/' + filename)

        elif child.is_file():
            print('Unpacking', iso_path + '/' + filename)
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
