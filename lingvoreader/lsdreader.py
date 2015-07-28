#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function, with_statement)
import sys
import os
import argparse
import codecs
from lingvoreader import decoder, tools

from lingvoreader.bitstream import BitStream, reverse16, reverse32

__author__ = 'sv99'
VERSION = '0.1'
#
# lsd decoder - based on source from tr7 user from ru-board
#   http://forum.ru-board.com/profile.cgi?action=show&member=tr7
# ru-board forum - "Lingvo dictionary"
#   http://forum.ru-board.com/topic.cgi?forum=93&topic=3774&glp#lt
#
# Worked with Lingvo x5 dictionary, other version not supported
#
# v 0.1 - 16.09.2013
#
if sys.platform.startswith("win"):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


class LsdError(Exception):
    pass


class OverlayReader():
    def __init__(self, bstr, offset):
        self.bstr = bstr

        if self.bstr.seek(offset):
            self._entriesCount = self.bstr.read_bits(4)
        else:
            self._entriesCount = 0

    def dump(self):
        print("Overlay:")
        print("\tEntriesCount:             %s" % self._entriesCount)


class Header():
    def __init__(self, bstr):
        self.bstr = bstr
        self.magic = self.bstr.read(8).replace('\x00', '')
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
        self.name = self.bstr.read_unicode(self.bstr.read_byte(), False)
        self.first_heading = self.bstr.read_unicode(self.bstr.read_byte(), False)
        self.last_heading = self.bstr.read_unicode(self.bstr.read_byte(), False)
        self.capitals = self.bstr.read_unicode(reverse32(self.bstr.read_int()), False)
        # icon
        self.icon_size = reverse16(self.bstr.read_word())
        # read icon
        self.icon = self.bstr.read(self.icon_size)
        self.header_checksum = reverse32(self.bstr.read_int())
        self.pages_end = reverse32(self.bstr.read_int())
        self.overlay_data = reverse32(self.bstr.read_int())
        return

    def dump(self, verbose):
        print("Header:")
        print("\tMagic:             %s" % self.magic)
        print("\tName:              %s" % self.name)
        print("\tVersion:           %s" % hex(self.version))
        print("\tEntries:           %d" % self.entries_count)
        print("\tSource language:   %d %s" % (self.source_language, tools.lang_map[self.source_language]))
        print("\tTarget language:   %d %s" % (self.target_language, tools.lang_map[self.target_language]))
        print("\tIcon enable:       %s" % (self.icon_size > 0))
        if verbose:
            print("\tFirst heading:     %s" % self.first_heading)
            print("\tLast heading:      %s" % self.last_heading)
            print("\tCapitals:          %s" % self.capitals)
            print("\tChecksume:         %s" % hex(self.header_checksum))
            print("\tPages count:       %d" % ((self.pages_end - self.pages_offset) // 512))
            print("\tAnnotationOffset:  %s" % hex(self.annotation_offset))
            print("\tDictionaryEncoderOffset: %s" % hex(self.dictionary_encoder_offset))
            print("\tArticlesOffset:    %s" % hex(self.articles_offset))
            print("\tPages start:       %s" % hex(self.pages_offset))
            print("\tPages end:         %s" % hex(self.pages_end))
            print("\tOverlay data:      %s" % hex(self.overlay_data))


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


class ArticleHeading():
    def __init__(self, decoder, bstr, known_prefix, version):
        self.text = ""
        self.extensions = []
        prefix_len = decoder.decode_prefix_len()
        postfix_len = decoder.decode_postfix_len()
        self.text = decoder.decode_heading(postfix_len)
        self.reference = decoder.read_reference2()
        self.text = known_prefix[:prefix_len] + self.text
        if version < 19:
            return
        if bstr.read_bit():
            # additional not visible formatting item in header
            # join multisymbols item
            ext_length = bstr.read_bits(8)
            if ext_length == 0:
                return
            ext = ""
            first_idx = prev_idx = 0
            for i in range(ext_length):
                idx = bstr.read_bits(8)
                char = unichr(bstr.read_bits(16))
                if ext == "":
                    ext += char
                    first_idx = prev_idx = idx
                else:
                    if prev_idx + 1 == idx:
                        # join item with sequence idx
                        ext += char
                        prev_idx = idx
                    else:
                        # other item
                        self.extensions.append((first_idx, ext))
                        ext = char
                        first_idx = prev_idx = idx
            # add last item
            self.extensions.append((first_idx, ext))
        return

    @property
    def ext_text(self):
        if len(self.extensions) == 0:
            return self.text
        res = self.text
        offset = 0
        for idx, ext in self.extensions:
            add_braces = ext != u"\\"
            if add_braces:
                ext = u"{" + ext + u"}"

            res = res[:idx + offset] + ext + res[idx + offset:]
            if add_braces:
                offset += 2
        return res


class LsdFile():
    def __init__(self, dict_file, mode="r"):
        """Open the Mobi file with mode read "r" or write "w" """
        if mode not in ("r", "w"):
            raise RuntimeError('MobiFile() requires mode "r" or "w"')
        self.filename = dict_file
        self.parsed = False
        self.verbose = False
        mode_dict = {'r': 'rb', 'w': 'wb'}
        with open(dict_file, mode_dict[mode]) as fp:
            self.bstr = BitStream(fp.read())

        self.header = Header(self.bstr)
        # only lsd
        if self.header.magic != 'LingVo':
            raise LsdError('Allow only Lsd "LingVo" ident: %s' % repr(self.header.magic))

        self.bstr.seek(self.header.dictionary_encoder_offset)
        version = self.header.version
        if version == 0x142001:  # user dictionaries
            self.decoder = decoder.UserDictionaryDecoder(self.bstr)
        elif version == 0x141004:  # system dictionaries
            self.decoder = decoder.SystemDictionaryDecoder(self.bstr)
        elif version == 0x145001:  # abbreviation dictionaries
            self.decoder = decoder.AbbreviationDictionaryDecoder(self.bstr)
        else:
            self.header.dump(True)
            raise LsdError("Not supported dict version %s" % hex(self.header.version))

        self.overlay = None
        self.headings = []
        self.dict = []

    @property
    def pages_count(self):
        return (self.header.pages_end - self.header.pages_offset) // 512

    def get_page_offset(self, page_number):
        return self.header.pages_offset + 512 * page_number

    def collect_headings(self):
        res = []
        for i in range(self.pages_count):
            headings = self.collect_heading_from_page(i)
            res += headings
        return res

    def collect_heading_from_page(self, page_number):
        res = []
        self.bstr.seek(self.get_page_offset(page_number))
        page = CachePage(self.bstr)
        if page.is_leaf:
            prefix = ""
            for idx in range(page.headings_count):
                heading = ArticleHeading(self.decoder, self.bstr, prefix, self.header.version)
                prefix = heading.text
                res.append(heading)
        return res

    def decode_article(self, reference):
        self.bstr.seek(self.header.articles_offset + reference)
        size = self.bstr.read_bits(16)
        if size == 0xFFFF:
            size = self.bstr.read_bits(32)

        res = self.decoder.decode_article(size)
        #assert(res)
        return res

    def parse(self):
        print("decoding dictionary..")
        self.overlay = OverlayReader(self.bstr, self.header.overlay_data)

        print("decoding headings: %d" % self.header.entries_count)
        self.headings = self.collect_headings()
        if len(self.headings) != self.header.entries_count:
            raise Exception("Decoded not all entries %d != %d" % (len(self.headings), self.header.entries_count))

        print("decoding articles..")
        for h in self.headings:
            self.dict.append((h.ext_text, self.decode_article(h.reference)))
        self.parsed = True
        print("OK")

    @property
    def annotation(self):
        res = ""
        if self.bstr.seek(self.header.annotation_offset):
            size = self.bstr.read_bits(16)
            res = self.decoder.decode_article(size)
        return res

    def dump(self):
        self.header.dump(self.verbose)
        self.decoder.dump(self.verbose)
        if self.verbose:
            self.overlay.dump()

    def make_filename(self, path, ext):
        base, orig_ext = os.path.splitext(self.filename)
        if path != "":
            base = os.path.join(path, os.path.basename(base))
        return base + '.' + ext

    def write_icon(self, path=""):
        if self.header.icon_size == 0:
            return
        ico_file = self.make_filename(path, "bmp")
        with open(ico_file, 'w') as ico:
            ico.write(self.header.icon)
        print('Write icon:       %s' % ico_file)

    def write_annotation(self, path=""):
        if self.annotation == "":
            return
        ann_file = self.make_filename(path, "ann")
        with codecs.open(ann_file, 'w', encoding='utf-16') as ann:
            ann.write(self.annotation)
        print('Write annotation: %s' % ann_file)

    def write_prefix(self, path=""):
        if self.annotation == "":
            return
        pref_file = self.make_filename(path, "pref")
        with codecs.open(pref_file, 'w', encoding='utf-8') as pref:
            pref.write(self.decoder.prefix)
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
            dsl.write(u"#NAME\t\"" + self.header.name + u"\"\n")
            dsl.write(u"#INDEX_LANGUAGE\t\"" + tools.lang_map[self.header.source_language] + u"\"\n")
            dsl.write(u"#CONTENTS_LANGUAGE\t\"" + tools.lang_map[self.header.target_language] + u"\"\n")
            if self.header.icon_size > 0:
                base, orig_ext = os.path.splitext(os.path.basename(self.filename))
                dsl.write(u"#ICON_FILE\t\"" + base + '.' + "bmp" + u"\"\n")
            dsl.write(u"\n")
            for h, r in self.dict:
                dsl.write(h)
                dsl.write(u"\n\t")
                dsl.write(self.normalize_article(r))
                dsl.write(u"\n")
        print('Write dsl:        %s' % dsl_file)

    def write(self, path=""):
        if not self.parsed:
            raise LsdError("Must parsed first!")
        self.write_icon(path)
        self.write_annotation(path)
        self.write_overlay(path)
        self.write_dsl(path)
        if self.verbose:
            self.write_prefix(path)


def unpack(dict_file, dest_dir, verbose):
    dict_ext = os.path.splitext(dict_file)[1].upper()

    if dict_ext != '.LSD':
        raise LsdError("Need Lingvo lsd dictionary.")

    try:
        print('Unpacking Dict...')
        m = LsdFile(dict_file)
        m.verbose = verbose
        m.parse()
        m.dump()
        m.write(dest_dir)
        print("Unpack %s OK" % dict_file)
    except ValueError, e:
        print("Error: %s" % e)
        return 1

    return 0


def get_dicts():
    current = os.getcwd()
    res = []
    for f in os.listdir(current):
        if f.endswith(".lsd"):
            res.append(f)
    return res


class CodecsAction(argparse.Action):

    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help="print supported languages and their codes"):
        super(CodecsAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit(message=tools.print_codecs())


def get_arg_parser():
    p = argparse.ArgumentParser(description='Decode Lingvo lsd dictionary to dsl')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("-i", "--input", help='Dictionary to decode')
    g.add_argument("-a", "--all", action="store_true", help='All dictionary in current directory')
    p.add_argument("-o", "--outdir", default="", help="Output directory")
    p.add_argument("-c", "--codecs", action=CodecsAction)
    p.add_argument("-v", "--verbose", action="store_true", default=False)
    p.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
    return p


def main():
    args = get_arg_parser().parse_args()
    dicts = []
    if args.all:
        # all lsd in directory
        print("Decode all lsd in current directory..")
        dicts = get_dicts()
        print(dicts)
    else:
        dicts.append(args.input)

    if args.outdir != "":
        # check path
        if not os.path.exists(args.outdir):
            os.mkdir(args.outdir)
    for d in dicts:
        unpack(d, args.outdir, args.verbose)

    return 0


if __name__ == '__main__':
    sys.exit(main())