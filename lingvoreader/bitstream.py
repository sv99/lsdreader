#!/usr/bin/env python
# -*- coding: utf-8 -*-
import struct

__author__ = 'sv99'


def reverse32(int_value):
    res, = struct.unpack('>L', struct.pack('<L', int_value))
    return res


def reverse16(word_value):
    res, = struct.unpack('>H', struct.pack('<H', word_value))
    return res


class BitStream():
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

    #def read_word_rev(self):
    #    res, = struct.unpack_from('<H', self.record, self.pos)
    #    self.pos += 2
    #    self.in_byte_pos = 0
    #    return res
    #
    #def read_int_rev(self):
    #    res, = struct.unpack_from('<L', self.record, self.pos)
    #    self.pos += 4
    #    self.in_byte_pos = 0
    #    return res
    #
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
            raise Exception("Many bits for read: %d" % count)
        res = 0
        for i in range(count):
            res <<= 1
            res += self.read_bit()
        return res

    def read_bits_o(self, count):
        if count > 32:
            raise Exception("Many bits for read: %d" % count)
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

    def read_unicode(self, size, big_endian=True):
        res = ""
        for i in range(size):
            if big_endian:
                ch = self.read_word()
            else:
                ch = reverse16(self.read_word())
            res += unichr(ch)
        return res