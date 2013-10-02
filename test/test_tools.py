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