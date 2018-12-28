# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import codecs
import os

from lingvoreader import LsdError
from lingvoreader import tools, decoder
from lingvoreader.articleheading import ArticleHeading, ArticleHeadingList
from lingvoreader.bitstream import reverse32, reverse16, BitStream

__author__ = 'sv99'


class OverlayReader:
    def __init__(self, bstr, offset):
        self.bstr = bstr

        if self.bstr.seek(offset):
            self._entriesCount = self.bstr.read_bits(4)
        else:
            self._entriesCount = 0

    def dump(self):
        print("Overlay:")
        print("    EntriesCount:      %s" % self._entriesCount)


class Header:
    def __init__(self, bstr):
        self.bstr = bstr
        self.magic = self.bstr.read(8).decode().replace('\x00', '')
        self.version = reverse32(self.bstr.read_int())
        self.unk = reverse32(self.bstr.read_int())
        self.checksum = reverse32(self.bstr.read_int())
        self.entries_count = reverse32(self.bstr.read_int())
        self.annotation_offset = reverse32(self.bstr.read_int())
        self.dictionary_encoder_offset = reverse32(self.bstr.read_int())
        self.articles_offset = reverse32(self.bstr.read_int())
        self.pages_offset = reverse32(self.bstr.read_int())
        self.unk1 = reverse32(self.bstr.read_int())
        self.unk2 = reverse16(self.bstr.read_word())
        self.unk3 = reverse16(self.bstr.read_word())
        self.source_language = reverse16(self.bstr.read_word())
        self.target_language = reverse16(self.bstr.read_word())
        return

    @property
    def hi_version(self):
        return self.version >> 16

    def dump(self):
        print("Header:")
        print("    Magic:             %s" % self.magic)
        print("    Checksume:         %s" % hex(self.checksum))
        print("    Version:           %s (%s)" % (hex(self.hi_version), hex(self.version)))
        print("    Entries:           %d" % self.entries_count)
        print("    AnnotationOffset:  %s" % hex(self.annotation_offset))
        print("    DictionaryEncoderOffset: %s" % hex(self.dictionary_encoder_offset))
        print("    ArticlesOffset:    %s" % hex(self.articles_offset))
        print("    Pages start:       %s" % hex(self.pages_offset))
        print("    Source language:   %d %s" % (self.source_language, tools.lang_map[self.source_language]))
        print("    Target language:   %d %s" % (self.target_language, tools.lang_map[self.target_language]))


class CachePage:
    def __init__(self, bstr):
        self.bstr = bstr
        self.is_leaf = bstr.read_bit()
        self.number = bstr.read_bits(16)
        self.prev = bstr.read_bits(16)
        self.parent = bstr.read_bits(16)
        self.next = bstr.read_bits(16)
        self.headings_count = bstr.read_bits(16)
        self.bstr.to_nearest_byte()
        return


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


class LsdFile:
    def __init__(self, dict_file, verbose=False):
        self.filename = dict_file
        self._readed = False
        self._parsed = False
        self.verbose = verbose
        with open(dict_file, 'rb') as fp:
            self.bstr = BitStream(bytearray(fp.read()))

        self.overlay = None
        self.headings = ArticleHeadingList()
        self.dict = []
        self.header = Header(self.bstr)
        # check magic
        if self.header.magic != u'LingVo':
            raise LsdError('Allow only Lsd "LingVo" ident: %s' % repr(self.header.magic))

        # initialize decoder
        self.decoder = None
        hi_version = self.header.hi_version
        version = self.header.version
        if hi_version == 0x11:  # lingvo 11 dictionary: 0x11001
            self.decoder = decoder.UserDictionaryDecoder(self.bstr)
        elif hi_version == 0x12:  # lingvo 12 dictionary: 0x12001
            self.decoder = decoder.UserDictionaryDecoder(self.bstr)
        elif hi_version == 0x13:  # x3 dictionary: 0x131001 and 0x132001 if pages count > 1000
            self.decoder = decoder.SystemDictionaryDecoder13(self.bstr)
        elif hi_version == 0x14:  # x5 dictionary
            if version == 0x142001:  # user dictionaries
                self.decoder = decoder.UserDictionaryDecoder(self.bstr)
            elif version == 0x141004:  # system dictionaries
                self.decoder = decoder.SystemDictionaryDecoder14(self.bstr)
            elif version == 0x145001:  # abbreviation dictionaries
                self.decoder = decoder.AbbreviationDictionaryDecoder(self.bstr)
        elif hi_version == 0x15:  # x6 dictionary
            if version == 0x152001:  # user dictionaries
                self.decoder = decoder.UserDictionaryDecoder(self.bstr)
            elif version == 0x151005:  # system dictionaries
                # xor dictionary
                self.xor_block_x6(self.header.dictionary_encoder_offset, self.header.articles_offset)
                self.decoder = decoder.SystemDictionaryDecoder14(self.bstr)
            elif version == 0x155001:  # abbreviation dictionaries
                self.decoder = decoder.AbbreviationDictionaryDecoder(self.bstr)

        if self.decoder is None:
            self.dump()
            print("Not supported dictionary version: %s" % hex(self.header.version))
            exit(1)
            # raise LsdError("Not supported dict version %s" % hex(self.header.version))

        name_len = self.bstr.read_some(1)
        self.name = self.bstr.read_unicode(name_len, False)
        self.first_heading = self.bstr.read_unicode(self.bstr.read_byte(), False)
        self.last_heading = self.bstr.read_unicode(self.bstr.read_byte(), False)
        capitals_len = reverse32(self.bstr.read_int())
        self.capitals = self.bstr.read_unicode(capitals_len, False)
        # icon v12+
        if self.header.version > 0x120000:
            self.icon_size = reverse16(self.bstr.read_word())
            self.icon = self.bstr.read(self.icon_size)
        else:
            self.icon_size = 0
            self.icon = None

        if self.header.version > 0x140000:
            self.header_checksum = reverse32(self.bstr.read_int())
        else:
            self.header_checksum = 0

        if self.header.version > 0x120000:
            self.pages_end = reverse32(self.bstr.read_int())
            self.overlay_data = reverse32(self.bstr.read_int())
        else:
            self.pages_end = self.bstr.length
            self.overlay_data = self.bstr.length  # no overlay

        if self.header.version > 0x140000:
            self.dummy1 = reverse32(self.bstr.read_int())
            self.dummy2 = reverse32(self.bstr.read_int())
        else:
            self.dummy1 = 0
            self.dummy2 = 0

        # set bstr pos for decoding
        self.bstr.seek(self.header.dictionary_encoder_offset)

    # x6 system dictionary table based xor decoding
    # each block xored with start key=0x7f
    # 1. dictionary_encoder_offset -> article_offset
    #    must by decoded befor decoder.read()
    # 2. annotation_offset -> dictionary_encoder_offset
    #    annotation decoded in the read_annotation
    # 3. each article encoded individully
    #    articles_offset + heading.reference -> articles_offset + heading.next-reference
    #    article decoded in the
    def xor_block_x6(self, start, end, key=0x7f):
        for i in range(start, end):
            byte = self.bstr.record[i]
            self.bstr.record[i] = byte ^ key
            key = xor_pad[byte]
        return key

    @property
    def pages_count(self):
        return (self.pages_end - self.header.pages_offset) // 512

    def get_page_offset(self, page_number):
        return self.header.pages_offset + 512 * page_number

    def read_headings(self):
        for i in range(self.pages_count):
            self.read_heading_from_page(i)
        # set last next_reference
        self.headings[-1].next_reference = self.header.pages_offset - self.header.articles_offset

    def merge_headings(self):
        res = []
        # fill next_reference in the headings
        prev = self.headings[0]
        res.append(prev)
        for i in range(1, len(self.headings)):
            h = self.headings[i]
            if prev.reference == h.reference:
                # multititle article
                prev.merge(h)
            else:
                res[-1].next_reference = h.reference
                res.append(h)
            prev = h
        # headings[i].next_reference = headings[i+1].reference
        # set next_reference for last item to the pages_offset
        res[-1].next_reference = self.header.pages_offset - self.header.articles_offset
        return res

    def read_heading_from_page(self, page_number):
        self.bstr.seek(self.get_page_offset(page_number))
        page = CachePage(self.bstr)
        if page.is_leaf:
            prefix = ""
            for idx in range(page.headings_count):
                heading = ArticleHeading()
                prefix = heading.read(self.decoder, self.bstr, prefix)
                self.headings.append(heading)

    def read_article(self, heading):
        self.bstr.seek(self.header.articles_offset + heading.reference)
        if self.header.version == 0x151005:
            # xor article
            self.xor_block_x6(self.header.articles_offset + heading.reference,
                              self.header.articles_offset + heading.next_reference)
        size = self.bstr.read_bits(16)
        if size == 0xFFFF:
            size = self.bstr.read_bits(32)

        res = self.decoder.decode_article(size)
        # assert(res)
        return res

    def read_annotation(self):
        if self.header.version == 0x151005:
            # xor annotation
            self.xor_block_x6(self.header.annotation_offset,
                              self.header.dictionary_encoder_offset)
        res = ""
        if self.bstr.seek(self.header.annotation_offset):
            size = self.bstr.read_bits(16)
            res = self.decoder.decode_article(size)
        return res

    @property
    def readed(self):
        return self._readed

    def read(self):
        if self.verbose:
            print("reading dictionary..")
        self.decoder.read()
        self._readed = True

    @property
    def parsed(self):
        return self._parsed

    def parse(self):
        if not self.readed:
            self.read()
        if self.verbose:
            print("decoding overlay..")
        self.overlay = OverlayReader(self.bstr, self.overlay_data)

        if self.verbose:
            print("decoding headings: %d" % self.header.entries_count)
        self.read_headings()
        if self.headings.appended != self.header.entries_count:
            raise LsdError("Decoded not all entries %d != %d" % (self.headings.appended, self.header.entries_count))
        # merge multititle headings
        # self.headings = self.merge_headings()

        if self.verbose:
            print("decoding articles: %d" % len(self.headings))
        for h in self.headings:
            # h.dump()
            self.dict.append((h, self.read_article(h)))
        self._parsed = True
        if self.verbose:
            print("OK")

    def write(self, path=""):
        """ save decoded dictionary """
        if not self.parsed:
            self.parse()
        self.write_icon(path)
        self.write_annotation(path)
        self.write_overlay(path)
        self.write_dsl(path)
        if self.verbose:
            self.write_prefix(path)

    def make_filename(self, path, ext):
        base, orig_ext = os.path.splitext(self.filename)
        if path != "":
            base = os.path.join(path, os.path.basename(base))
        return base + '.' + ext

    def write_icon(self, path=""):
        if self.icon_size == 0:
            return
        ico_file = self.make_filename(path, "bmp")
        with open(ico_file, 'wb') as ico:
            ico.write(self.icon)
        if self.verbose:
            print('Write icon:       %s' % ico_file)

    def write_annotation(self, path=""):
        annotation = self.read_annotation()
        if annotation == "":
            return
        ann_file = self.make_filename(path, "ann")
        with codecs.open(ann_file, 'w', encoding='utf-16') as ann:
            ann.write(annotation)
        if self.verbose:
            print('Write annotation: %s' % ann_file)

    def write_prefix(self, path=""):
        if self.decoder.prefix == "":
            return
        pref_file = self.make_filename(path, "pref")
        with codecs.open(pref_file, 'w', encoding='utf-8') as pref:
            pref.write(self.decoder.prefix)
        if self.verbose:
            print('Write prefix:     %s' % pref_file)

    def write_overlay(self, path=""):
        pass

    @staticmethod
    def normalize_article(article):
        res = article.replace(u'\n', u'\n\t')
        return res

    def write_dsl(self, path=""):
        if len(self.dict) == 0:
            print("Nothing writing to dsl!")
            return
        dsl_file = self.make_filename(path, "dsl")
        with codecs.open(dsl_file, 'w', encoding='utf-16') as dsl:
            dsl.write(u"#NAME\t\"" + self.name + u"\"\n")
            dsl.write(u"#INDEX_LANGUAGE\t\"" + tools.lang_map[self.header.source_language] + u"\"\n")
            dsl.write(u"#CONTENTS_LANGUAGE\t\"" + tools.lang_map[self.header.target_language] + u"\"\n")
            if self.icon_size > 0:
                base, orig_ext = os.path.splitext(os.path.basename(self.filename))
                dsl.write(u"#ICON_FILE\t\"" + base + '.' + "bmp" + u"\"\n")
            dsl.write(u"\n")
            for h, r in self.dict:
                if h.simple:
                    dsl.write(h.get_first_ext_text())
                    dsl.write(u"\n\t")
                else:
                    for item in h.headings:
                        dsl.write(item.ext_text)
                        dsl.write(u"\n")
                    dsl.write(u"\t")
                dsl.write(self.normalize_article(r))
                dsl.write(u"\n")
        if self.verbose:
            print('Write dsl:        %s' % dsl_file)

    def dump(self):
        self.header.dump()
        # dump header for not supported versions
        if self.decoder is not None:
            print("Name:                  %s" % self.name)
            print("First heading:         %s" % self.first_heading)
            print("Last heading:          %s" % self.last_heading)
            print("Capitals:              %s" % self.capitals)
            print("Pages end:             %s" % hex(self.pages_end))
            print("Overlay data:          %s" % hex(self.overlay_data))
            print("Pages count:           %d" % ((self.pages_end - self.header.pages_offset) // 512))
            if self.header.version > 0x140000:
                print("dummy1:                %s" % hex(self.dummy1))
                print("dummy2:                %s" % hex(self.dummy2))
            print("Icon enable:           %s" % (self.icon_size > 0))
            if self.readed:
                self.decoder.dump()
                self.overlay.dump()
