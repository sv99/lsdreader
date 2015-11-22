lingvoreader
============

python analog ABBYY DSL Compiler x5 - decomile LSD dictionary to DSL.

Based on C++ source lsd2dsl from ru-board user tr7_

.. _tr7: http://forum.ru-board.com/profile.cgi?action=show&member=tr7

Source on github: https://github.com/nongeneric/lsd2dsl

Project Page: https://github.com/sv99/lsdreader

Build
-----

    python setup.py sdist upload

For PyPi upload needs configuration file ~/.pypirc

Install
-------

Install a package:

::

    easy_install lingvoreader-0.1.4-py2.7.egg

or

::

    pip install lingvoreader

Usage
-----

::

    lsdreader [-h] (-i INPUT | -a) [-o OUTDIR] [-c] [-v] [--version]

    Decode Lingvo X5 lsd dictionary to dsl

    optional arguments:

        -h, --help            show this help message and exit
        -header               show header info and exit
        -i INPUT, --input INPUT  Dictionary to decode
        -a, --all             All dictionary in current directory
        -o OUTDIR, --outdir OUTDIR  Output directory
        -c, --codecs          print supported languages and their codes
        -v, --verbose
        --version             show program's version number and exit
