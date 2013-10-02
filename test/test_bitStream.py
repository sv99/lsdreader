#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
from lingvoreader import bitstream

__author__ = 'sv99'


class TestBitStream(TestCase):
    def setUp(self):
        print "Creating a new BitStream..."
        self.record = '\x00\x01\x02\x03\x04\x05\x06\x07\x08'
        self.bst = bitstream.BitStream(self.record)

    def tearDown(self):
        print "Destroying the BitStream..."
        self.bst = None

    def test_reverse32(self):
        self.assertEqual(bitstream.reverse32(0x01020304), 0x04030201)

    def test_reverse16(self):
        self.assertEqual(bitstream.reverse16(0x0102), 0x0201)

    def test_length(self):
        self.assertEqual(len(self.record), self.bst.length)

    def test_to_nearest_byte(self):
        self.bst.seek(0)
        self.bst.to_nearest_byte()
        self.assertEqual(self.bst.pos, 0)
        self.bst.read_bit()
        self.bst.to_nearest_byte()
        self.assertEqual(self.bst.pos, 1)

    def test_read_byte(self):
        self.bst.seek(0)
        self.assertEqual(self.bst.read_byte(), 0)
        self.bst.seek(1)
        self.assertEqual(self.bst.read_byte(), 1)

    def test_read_word(self):
        self.bst.seek(1)
        self.assertEqual(self.bst.read_word(), 0x0102)

    def test_read_int(self):
        self.bst.seek(1)
        self.assertEqual(self.bst.read_int(), 0x01020304)

    #def test_read_symbols(self):
    #    self.fail()

    def test_read_bit(self):
        self.bst.seek(1)
        self.bst.read_bits(7)
        self.assertEqual(self.bst.read_bit(), 1)
        self.assertEqual(self.bst.read_bit(), 0)

    def test_read_bits(self):
        self.bst.seek(1)
        self.assertEqual(self.bst.read_bits(4), 0)
        self.assertEqual(self.bst.read_bits(4), 1)
        self.assertEqual(self.bst.read_bits(4), 0)
        self.assertEqual(self.bst.read_bits(8), 0x20)