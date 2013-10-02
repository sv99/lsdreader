#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function)
from lingvoreader import tools
from lingvoreader.lentable import LenTable

__author__ = 'sv99'


class Decoder():
    def __init__(self, bstr):
        self.bstr = bstr
        self.prefix = ""
        self._article_symbols = None
        self._heading_symbols = None
        self._ltArticles = None
        self._ltHeadings = None
        self._ltPrefixLengths = None
        self._ltPostfixLengths = None
        self._huffman1Number = 0
        self._huffman2Number = 0

    def decode_prefix_len(self):
        return self._ltPrefixLengths.decode()

    def decode_postfix_len(self):
        return self._ltPostfixLengths.decode()

    def read_reference1(self):
        return self.read_reference(self._huffman2Number)

    def read_reference2(self):
        return self.read_reference(self._huffman2Number)

    def read_reference(self, huffman_number):
        reference = ""
        code = self.bstr.read_bits(2)
        if code == 3:
            self.bstr.read_bits(32)
            return reference

        size = tools.bit_length(huffman_number)
        assert(size >= 2)
        return (code << (size - 2)) | self.bstr.read_bits(size - 2)

    def decode_article(self, size):
        """
        decode User and Abrv dict
        """
        res = ""
        while len(res) < size:
            sym_idx = self._ltArticles.decode()
            sym = self._article_symbols[sym_idx]
            if sym >= 0x10000:
                if sym >= 0x10040:
                    start_idx = self.bstr.read_bits(tools.bit_length(size))
                    s = sym - 0x1003d
                    res += res[start_idx:start_idx + s]
                else:
                    prefix_idx = self.bstr.read_bits(tools.bit_length(len(self.prefix)))
                    s = sym - 0xfffd
                    res += self.prefix[prefix_idx:prefix_idx + s]
            else:
                res += unichr(sym)
        return res

    def dump(self, verbose):
        print("Decoder:             %s" % self.__class__.__name__)
        if verbose:
            print("\tArticleSymbols:    %d" % len(self._article_symbols))
            print("\tHeadingSymbols:    %d" % len(self._heading_symbols))
            self._ltArticles.dump("Articles")
            self._ltHeadings.dump("Headings")
            self._ltPrefixLengths.dump("PrefixLengths")
            self._ltPostfixLengths.dump("PostfixLengths")


class UserDictionaryDecoder(Decoder):
    def __init__(self, bstr):
        Decoder.__init__(self, bstr)
        self.prefix = self.bstr.read_unicode(self.bstr.read_int())
        self._article_symbols = self.bstr.read_symbols()
        self._heading_symbols = self.bstr.read_symbols()
        self._ltArticles = LenTable(self.bstr)
        self._ltHeadings = LenTable(self.bstr)
        self._ltPrefixLengths = LenTable(self.bstr)
        self._ltPostfixLengths = LenTable(self.bstr)
        self._huffman1Number = self.bstr.read_bits(32)
        self._huffman2Number = self.bstr.read_bits(32)
        return

    def decode_heading(self, size):
        res = ""
        for i in range(size):
            sym_idx = self._ltHeadings.decode()
            sym = self._heading_symbols[sym_idx]
            assert(sym <= 0xffff)  # LingvoEngine:2EAB84E8
            res += unichr(sym)
        return res


class SystemDictionaryDecoder(Decoder):
    def __init__(self, bstr):
        Decoder.__init__(self, bstr)
        self.prefix = self.bstr.read_unicode(self.bstr.read_int())
        self._article_symbols = self.bstr.read_symbols()
        self._heading_symbols = self.bstr.read_symbols()
        self._ltArticles = LenTable(self.bstr)
        self._ltHeadings = LenTable(self.bstr)

        self._ltPostfixLengths = LenTable(self.bstr)
        self._dummy = self.bstr.read_bits(32)
        self._ltPrefixLengths = LenTable(self.bstr)

        self._huffman1Number = self.bstr.read_bits(32)
        self._huffman2Number = self.bstr.read_bits(32)
        return

    def decode_heading(self, size):
        res = ""
        for i in range(size):
            sym_idx = self._ltHeadings.decode()
            sym = self._heading_symbols[sym_idx]
            assert(sym <= 0xffff)  # LingvoEngine:2EAB84E8
            res += unichr(sym)
        return res

    def decode_article(self, size):
        res = ""
        while len(res) < size:
            sym_idx = self._ltArticles.decode()
            sym = self._article_symbols[sym_idx]
            if sym <= 0x80:
                if sym <= 0x3F:
                    start_pref_idx = self.bstr.read_bits(tools.bit_length(len(self.prefix)))
                    s = sym + 3
                    res += self.prefix[start_pref_idx:start_pref_idx + s]
                else:
                    start_idx = self.bstr.read_bits(tools.bit_length(size))
                    s = sym - 0x3d
                    res += res[start_idx:start_idx + s]
            else:
                res += unichr(sym - 0x80)
        return res


class AbbreviationDictionaryDecoder(Decoder):
    def __init__(self, bstr):
        Decoder.__init__(self, bstr)
        self.prefix = self.read_xored_prefix(self.bstr.read_int())
        self._article_symbols = self.read_xored_symbols()
        self._heading_symbols = self.read_xored_symbols()
        self._ltArticles = LenTable(self.bstr)
        self._ltHeadings = LenTable(self.bstr)

        self._ltPrefixLengths = LenTable(self.bstr)
        self._ltPostfixLengths = LenTable(self.bstr)

        self._huffman1Number = self.bstr.read_bits(32)
        self._huffman2Number = self.bstr.read_bits(32)
        return

    def read_xored_symbols(self):
        size = self.bstr.read_bits(32)
        bits_per_symbol = self.bstr.read_bits(8)
        res = []
        for i in range(size):
            res.append(self.bstr.read_bits(bits_per_symbol) ^ 0x1325)
        return res

    def read_xored_prefix(self, size):
        res = ""
        for i in range(size):
            res += unichr(self.bstr.read_bits(16) ^ 0x879A)
        return res

    def decode_heading(self, size):
        res = ""
        for i in range(size):
            sym_idx = self._ltHeadings.decode()
            sym = self._heading_symbols[sym_idx]
            assert(sym <= 0xffff)  # LingvoEngine:2EAB84E8
            res += unichr(sym)
        return res