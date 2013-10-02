#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (print_function)
import tools

__author__ = 'sv99'


class SymInfo():
    def __init__(self, sym_idx, size, code):
        self.sym_idx = sym_idx
        self.size = size
        self.code = code


class HuffmanNode():
    def __init__(self, left, right, parent, weight):
        self.left = left
        self.right = right
        self.parent = parent
        self.weight = weight


class LenTable():
    def __init__(self, bstr):
        self.bstr = bstr
        self._count = self.bstr.read_bits(32)
        self._bits_per_len = self.bstr.read_bits(8)
        self._idx_bit_size = tools.bit_length(self._count)

        self.symidx2nodeidx = [-1 for _ in range(self._count)]
        self.nodes = [HuffmanNode(0, 0, -1, -1) for _ in range(self._count - 1)]
        root_idx = len(self.nodes) - 1
        self.next_node_position = 0
        for i in range(self._count):
            symidx = self.bstr.read_bits(self._idx_bit_size)
            length = self.bstr.read_bits(self._bits_per_len)
            self.place_sym_idx(symidx, root_idx, length)

    def place_sym_idx(self, sym_idx, node_idx, size):
        assert size > 0
        if size == 1:  # time to place
            if self.nodes[node_idx].left == 0:
                self.nodes[node_idx].left = -1 - sym_idx
                self.symidx2nodeidx[sym_idx] = node_idx
                return True

            if self.nodes[node_idx].right == 0:
                self.nodes[node_idx].right = -1 - sym_idx
                self.symidx2nodeidx[sym_idx] = node_idx
                return True

            return False

        if self.nodes[node_idx].left == 0:
            self.nodes[self.next_node_position] = HuffmanNode(0, 0, node_idx, -1)
            self.next_node_position += 1
            self.nodes[node_idx].left = self.next_node_position

        if self.nodes[node_idx].left > 0:
            if self.place_sym_idx(sym_idx, self.nodes[node_idx].left - 1, size - 1):
                return True

        if self.nodes[node_idx].right == 0:
            self.nodes[self.next_node_position] = HuffmanNode(0, 0, node_idx, -1)
            self.next_node_position += 1
            self.nodes[node_idx].right = self.next_node_position

        if self.nodes[node_idx].right > 0:
            if self.place_sym_idx(sym_idx, self.nodes[node_idx].right - 1, size - 1):
                return True

        return False

    def decode(self):
        node = self.nodes[-1]
        length = 0
        while True:
            length += 1
            bit = self.bstr.read_bit()
            if bit:  # right
                if node.right < 0:  # leaf
                    sym_idx = -1 - node.right
                    return sym_idx
                node = self.nodes[node.right - 1]
            else:  # left
                if node.left < 0:  # leaf
                    sym_idx = -1 - node.left
                    return sym_idx

                node = self.nodes[node.left - 1]

    def dump(self, name):
        print("LenTable:            %s" % name)
        print("\tCount:             %s" % self._count)
        print("\tbitsPerLen:        %s" % self._bits_per_len)
        print("\tIdxBitSize:        %s" % self._idx_bit_size)