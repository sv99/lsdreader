#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
from lingvoreader import tools

__author__ = 'sv99'


class TestTools(TestCase):
    def test_bit_length_0(self):
        self.assertEqual(tools.bit_length(0), 1)

    def test_bit_length_1(self):
        self.assertEqual(tools.bit_length(1), 1)

    def test_bit_length_2(self):
        self.assertEqual(tools.bit_length(2), 2)

    def test_bit_length_4(self):
        self.assertEqual(tools.bit_length(4), 3)

    def test_display_time(self):
        self.assertEquals(tools.display_time(1),
                          "1.00 sec")
        self.assertEquals(tools.display_time(61.2),
                          "1 min 1.20 sec")
        self.assertEquals(tools.display_time(60),
                          "1 min 0.00 sec")
        self.assertEquals(tools.display_time(3600),
                          "1 hour 0.00 sec")
        self.assertEquals(tools.display_time(3661),
                          "1 hour 1 min 1.00 sec")
