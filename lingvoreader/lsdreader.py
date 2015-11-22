#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function, with_statement)

import argparse
import codecs
import os
import sys
from timeit import default_timer as timer

from lingvoreader import __version__
from lingvoreader import LsdError
from lingvoreader import tools
from lingvoreader.lsdfile import LsdFile

__author__ = 'sv99'

#
# lsd decoder - based on source from tr7 user from ru-board
#   http://forum.ru-board.com/profile.cgi?action=show&member=tr7
# ru-board forum - "Lingvo dictionary"
#   http://forum.ru-board.com/topic.cgi?forum=93&topic=3774&glp#lt
# current version on the github https://github.com/nongeneric/lsd2dsl
#
# Worked with Lingvo x5 dictionary, other version not supported
# v 0.1 - 16.09.2013
#
# v 0.1.6 - 19.11.2015
#   add support lingvo 12 and x3 dictionary format
#
if sys.platform.startswith("win"):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


def unpack(dict_file, dest_dir, verbose):
    dict_ext = os.path.splitext(dict_file)[1].upper()

    if dict_ext != '.LSD':
        raise LsdError("Need Lingvo lsd dictionary.")

    start = timer()
    try:
        print("Unpacking dict: %s" % dict_file)
        m = LsdFile(dict_file, verbose)
        m.parse()
        m.dump()
        m.write(dest_dir)
    except ValueError, e:
        print("Error: %s" % e)
        return 1
    end = timer()
    print("Unpack OK (%s)" % tools.display_time(end - start))

    return 0


def header(dict_file):
    dict_ext = os.path.splitext(dict_file)[1].upper()

    if dict_ext != '.LSD':
        raise LsdError("Need Lingvo lsd dictionary.")

    try:
        print("Unpacking dict: %s" % dict_file)
        m = LsdFile(dict_file, True)
        m.dump()
        # print("Header %s OK" % dict_file)
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
    p.add_argument("--header", action="store_true", default=False, help='Print dictionary header and exit')
    p.add_argument("-o", "--outdir", default="", help="Output directory")
    p.add_argument("-c", "--codecs", action=CodecsAction)
    p.add_argument("-v", "--verbose", action="store_true", default=False)
    p.add_argument('--version', action='version', version='%(prog)s ' + __version__)
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

    if args.header:
        for d in dicts:
            header(d)
        return 0

    if args.outdir != "":
        # check path
        if not os.path.exists(args.outdir):
            os.mkdir(args.outdir)

    start = timer()
    c = 0
    for d in dicts:
        unpack(d, args.outdir, args.verbose)
        c += 1
    end = timer()
    if c > 1:
        print("Files count: %i" % c)
        print("Elapsed: %s" % tools.display_time(end - start))

    return 0


if __name__ == '__main__':
    sys.exit(main())
