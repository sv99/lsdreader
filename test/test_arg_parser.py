#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
from lingvoreader import lsdreader
import sys
from StringIO import StringIO

__author__ = 'sv99'


class ArgumentParserError(Exception):

    def __init__(self, message, stdout=None, stderr=None, error_code=None):
        Exception.__init__(self, message, stdout, stderr)
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        self.error_code = error_code


class StdIOBuffer(StringIO):
    pass


def stderr_to_parser_error(parse_args, *args, **kwargs):
    # if this is being called recursively and stderr or stdout is already being
    # redirected, simply call the function and let the enclosing function
    # catch the exception
    if isinstance(sys.stderr, StdIOBuffer) or isinstance(sys.stdout, StdIOBuffer):
        return parse_args(*args, **kwargs)

    # if this is not being called recursively, redirect stderr and
    # use it as the ArgumentParserError message
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StdIOBuffer()
    sys.stderr = StdIOBuffer()
    try:
        try:
            result = parse_args(*args, **kwargs)
            for key in list(vars(result)):
                if getattr(result, key) is sys.stdout:
                    setattr(result, key, old_stdout)
                if getattr(result, key) is sys.stderr:
                    setattr(result, key, old_stderr)
            return result
        except SystemExit:
            code = sys.exc_info()[1].code
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
            raise ArgumentParserError("SystemExit", stdout, stderr, code)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class TestArgParser(TestCase):
    def setUp(self):
        self.parser = lsdreader.get_arg_parser()

    def test_empty(self):
        self.assertRaisesRegexp(ArgumentParserError,
                                'one of the arguments -i/--input -a/--all is required',
                                stderr_to_parser_error, self.parser.parse_args, [])

    def test_codecs(self):
        self.assertRaisesRegexp(ArgumentParserError,
                                "SystemExit",
                                stderr_to_parser_error, self.parser.parse_args, ['-c', ])

    def test_input(self):
        args = self.parser.parse_args('-i test'.split())
        self.assertEqual(args.input, 'test')
        self.assertFalse(args.verbose)

    def test_input_verbose(self):
        args = self.parser.parse_args('-i test -v'.split())
        self.assertEqual(args.input, 'test')
        self.assertTrue(args.verbose)
        self.assertEqual(args.outdir, '')

    def test_all(self):
        args = self.parser.parse_args('-a'.split())
        self.assertTrue(args.all)
        self.assertFalse(args.verbose)
        self.assertEqual(args.outdir, '')

    def test_all_verbose(self):
        args = self.parser.parse_args('-a -v'.split())
        self.assertTrue(args.all)
        self.assertTrue(args.verbose)
        self.assertEqual(args.outdir, '')

    def test_outdir(self):
        args = self.parser.parse_args('-a -o test'.split())
        self.assertTrue(args.all)
        self.assertFalse(args.verbose)
        self.assertEqual(args.outdir, 'test')
