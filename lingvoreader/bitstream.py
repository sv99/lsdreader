#!/usr/bin/env python
# -*- coding: utf-8 -*-
import struct

from lingvoreader import LsdError

__author__ = 'sv99'


def reverse32(int_value):
    res, = struct.unpack('>L', struct.pack('<L', int_value))
    return res


def reverse16(word_value):
    res, = struct.unpack('>H', struct.pack('<H', word_value))
    return res

def rec2word(rec, big_endian=True):
    if big_endian:
        return (ord(rec[0]) << 8) + ord(rec[1])
    else:
        return (ord(rec[1]) << 8) + ord(rec[0])

def rec2int(rec, big_endian=True):
    if big_endian:
        return (ord(rec[0]) << 24) + (ord(rec[1]) << 16) + (ord(rec[2]) << 8) + ord(rec[3])
    else:
        return (ord(rec[3]) << 24) + (ord(rec[2]) << 16) + (ord(rec[1]) << 8) + ord(rec[0])


class BitStream:
    def __init__(self, record):
        self.record = record
        self.pos = 0
        self.in_byte_pos = 0  # start from highest to smallest
        return

    @property
    def length(self):
        return len(self.record)

    def seek(self, pos):
        self.pos = pos
        self.in_byte_pos = 0
        return pos < self.length

    def read(self, length):
        current = self.pos
        self.pos += length
        return self.record[current:self.pos]

    def to_nearest_byte(self):
        """
        move to start next byte, if needed
        """
        if self.in_byte_pos != 0:
            self.in_byte_pos = 0
            self.pos += 1

    def read_byte(self):
        res, = struct.unpack_from('B', self.record, self.pos)
        self.pos += 1
        self.in_byte_pos = 0
        return res

    # def read_word_rev(self):
    #    res, = struct.unpack_from('<H', self.record, self.pos)
    #    self.pos += 2
    #    self.in_byte_pos = 0
    #    return res
    #
    # def read_int_rev(self):
    #    res, = struct.unpack_from('<L', self.record, self.pos)
    #    self.pos += 4
    #    self.in_byte_pos = 0
    #    return res

    def read_word(self):
        res, = struct.unpack_from('>H', self.record, self.pos)
        self.pos += 2
        self.in_byte_pos = 0
        return res

    def read_int(self):
        res, = struct.unpack_from('>L', self.record, self.pos)
        self.pos += 4
        self.in_byte_pos = 0
        return res

    def read_symbols(self):
        size = self.read_bits(32)
        bits_per_symbol = self.read_bits(8)
        res = []
        for i in range(size):
            res.append(self.read_bits(bits_per_symbol))
        return res

    def read_bit(self):
        byte, = struct.unpack_from('B', self.record, self.pos)
        byte >>= (7 - self.in_byte_pos)
        if self.in_byte_pos == 7:
            self.pos += 1
            self.in_byte_pos = 0
        else:
            self.in_byte_pos += 1
        return byte & 1

    def read_bits(self, count):
        return self.read_bits_o(count)

    # stupid direct implementation
    def read_bits_s(self, count):
        if count > 32:
            raise LsdError("Many bits for read: %d" % count)
        res = 0
        for i in range(count):
            res <<= 1
            res += self.read_bit()
        return res

    def read_bits_o(self, count):
        if count > 32:
            raise LsdError("Many bits for read: %d" % count)
        masks = (1, 3, 7, 0xF, 0x1F, 0x3F, 0x7F, 0xFF)
        count_bytes = (count + self.in_byte_pos) // 8
        if count + self.in_byte_pos - 8 * count_bytes > 0:
            count_bytes += 1
        # if in single raw byt
        if count_bytes == 1:
            if (self.in_byte_pos + count) < 8:
                byte = ord(self.record[self.pos])
                byte >>= 7 - self.in_byte_pos - count + 1
                byte &= masks[count - 1]
                self.in_byte_pos += count
                return byte
        # many raw bytes
        #   inBitPos
        #      |   count = 13    |
        # 01234567 | 01234567 | 0123456
        #
        # inBitPos = 5 count_first = 3 count_las = 2
        #
        p = self.pos
        count_last = (count + self.in_byte_pos) % 8
        count_first = 8 - self.in_byte_pos
        byte_first = ord(self.record[p])
        p += 1
        byte_first &= masks[count_first - 1]
        res = byte_first
        # full bytes
        full_bytes = (count - count_first) // 8
        if full_bytes > 0:
            for i in range(full_bytes):
                res <<= 8
                res += ord(self.record[p])
                p += 1
        # last byte
        if count_last > 0:
            byte = ord(self.record[p])
            byte >>= 8 - count_last
            res <<= count_last
            res += byte
        self.in_byte_pos = count_last
        self.pos = p
        return res

    def read_some(self, length):
        if length == 1:
            return self.read_byte()
        elif length == 2:
            return self.read_word()
        elif length == 4:
            return self.read_int()
        else:
            raise LsdError('Allow read byte, word and int length: %i' % length)

    def read_unicode(self, size, big_endian=True):
        res = ""
        for i in range(size):
            if big_endian:
                ch = self.read_some(2)
            else:
                ch = reverse16(self.read_some(2))
            res += unichr(ch)
            # res += unichr(self.read_some(2), big_endian))
        return res


xor_pad = (
    0x9C, 0xDF, 0x9B, 0xF3, 0xBE, 0x3A, 0x83, 0xD8,
    0xC9, 0xF5, 0x50, 0x98, 0x35, 0x4E, 0x7F, 0xBB,
    0x89, 0xC7, 0xE9, 0x6B, 0xC4, 0xC8, 0x4F, 0x85,
    0x1A, 0x10, 0x43, 0x66, 0x65, 0x57, 0x55, 0x54,
    0xB4, 0xFF, 0xD7, 0x17, 0x06, 0x31, 0xAC, 0x4B,
    0x42, 0x53, 0x5A, 0x46, 0xC5, 0xF8, 0xCA, 0x5E,
    0x18, 0x38, 0x5D, 0x91, 0xAA, 0xA5, 0x58, 0x23,
    0x67, 0xBF, 0x30, 0x3C, 0x8C, 0xCF, 0xD5, 0xA8,
    0x20, 0xEE, 0x0B, 0x8E, 0xA6, 0x5B, 0x49, 0x3F,
    0xC0, 0xF4, 0x13, 0x80, 0xCB, 0x7B, 0xA7, 0x1D,
    0x81, 0x8B, 0x01, 0xDD, 0xE3, 0x4C, 0x9A, 0xCE,
    0x40, 0x72, 0xDE, 0x0F, 0x26, 0xBD, 0x3B, 0xA3,
    0x05, 0x37, 0xE1, 0x5F, 0x9D, 0x1E, 0xCD, 0x69,
    0x6E, 0xAB, 0x6D, 0x6C, 0xC3, 0x71, 0x1F, 0xA9,
    0x84, 0x63, 0x45, 0x76, 0x25, 0x70, 0xD6, 0x8F,
    0xFD, 0x04, 0x2E, 0x2A, 0x22, 0xF0, 0xB8, 0xF2,
    0xB6, 0xD0, 0xDA, 0x62, 0x75, 0xB7, 0x77, 0x34,
    0xA2, 0x41, 0xB9, 0xB1, 0x74, 0xE4, 0x95, 0x1B,
    0x3E, 0xE7, 0x00, 0xBC, 0x93, 0x7A, 0xE8, 0x86,
    0x59, 0xA0, 0x92, 0x11, 0xF7, 0xFE, 0x03, 0x2F,
    0x28, 0xFA, 0x27, 0x02, 0xE5, 0x39, 0x21, 0x96,
    0x33, 0xD1, 0xB2, 0x7C, 0xB3, 0x73, 0xC6, 0xE6,
    0xA1, 0x52, 0xFB, 0xD4, 0x9E, 0xB0, 0xE2, 0x16,
    0x97, 0x08, 0xF6, 0x4A, 0x78, 0x29, 0x14, 0x12,
    0x4D, 0xC1, 0x99, 0xBA, 0x0D, 0x3D, 0xEF, 0x19,
    0xAF, 0xF9, 0x6F, 0x0A, 0x6A, 0x47, 0x36, 0x82,
    0x07, 0x9F, 0x7D, 0xA4, 0xEA, 0x44, 0x09, 0x5C,
    0x8D, 0xCC, 0x87, 0x88, 0x2D, 0x8A, 0xEB, 0x2C,
    0xB5, 0xE0, 0x32, 0xAD, 0xD3, 0x61, 0xAE, 0x15,
    0x60, 0xF1, 0x48, 0x0E, 0x7E, 0x94, 0x51, 0x0C,
    0xEC, 0xDB, 0xD2, 0x64, 0xDC, 0xFC, 0xC2, 0x56,
    0x24, 0xED, 0x2B, 0xD9, 0x1C, 0x68, 0x90, 0x79
)

class XoredBitStream(BitStream):
    def __init__(self, bstr):
        BitStream.__init__(self, bstr.record)
        self.pos = bstr.pos
        self.in_byte_pos = bstr.in_byte_pos
        self.key = 0x7f
        self.decode()
        return

    def seek(self, pos):
        self.key = 0x7f
        return BitStream.seek(self, pos)

    def decode(self):
        res = ""
        for i in range(self.pos, self.length):
            byte = ord(self.record[i])
            res += chr(byte ^ self.key)
            self.key = xor_pad[byte]
        self.record = self.record[:self.pos] + res
    # def read_some(self, length):
    #     current = self.pos
    #     self.pos += length
    #     bytes = self.record[current:self.pos]
    #     res = 0
    #     for i in range(length):
    #         byte = ord(bytes[i])
    #         res <<= 8
    #         res += byte ^ self.key
    #         self.key = xor_pad[byte]
    #     return res

    # def read_unicode(self, size, big_endian=True):
    #     res = ""
    #     for i in range(size):
    #         if big_endian:
    #             ch = self.read_some(2)
    #         else:
    #             ch = reverse16(self.read_some(2))
    #         res += unichr(ch)
    #         # res += unichr(rec2word(self.read_some(2), big_endian))
    #     return res

    # def read_symbols(self):
    #     size = self.read_some(4)
    #     bits_per_symbol = self.read_some(1)
    #     res = []
    #     for i in range(size):
    #         sym = self.read_bits(bits_per_symbol)
    #         # byte = sym & 0xff
    #         # val = byte ^ self.key
    #         # val <<= 8
    #         # self.key = xor_pad[byte]
    #         # byte = sym >> 8
    #         # val += byte ^ self.key
    #         # self.key = xor_pad[byte]
    #         res.append(sym)
    #     return res

