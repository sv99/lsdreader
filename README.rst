lsdreader
=========

python analog ABBYY DSL Compiler - decompile LSD dictionary to DSL.

Support Lingvo 11, 12, X3, X5 and X6 lsd files format.

Based on C++ source decoder.zip from ru-board user `tr7 <http://forum.ru-board.com/profile.cgi?action=show&member=tr7>`_
`Source on github <https://github.com/nongeneric/lsd2dsl>`_

Russian decompiling team on `ru-board.ru <http://forum.ru-board.com/topic.cgi?forum=93&topic=3774>`_

Project Page: https://github.com/sv99/lsdreader

Install
=======

Install from pip::

    pip install setuptools -U
    pip install lingvoreader

Install development version::

    git clone 
    pip install -e .
    
make tar.gz for PyPi::
    
    pip install twine
    python setup.py sdist
    twine upload dist/lingvoreader-x.x.x.tar.gz

Usage
-----
::

    lsdreader [-h] [--header] (-i INPUT | -a) [-o OUTDIR] [-c] [-v] [--version]
    
    Decode Lingvo 11, 12, X3, X5 and X6 lsd dictionary to dsl
    
    optional arguments:
      -h, --help            show this help message and exit
      --header              show header info and exit
      -i INPUT, --input INPUT
                            Dictionary to decode
      -a, --all             All dictionary in current directory
      -o OUTDIR, --outdir OUTDIR
                            Output directory
      -c, --codecs          print supported languages and their codes
      -v, --verbose
      --version             show program's version number and exit

Lingvo versions
===============

::

    11  2005  supported
    12  2006  supported
    x3  2008  supported
    x5  2011  supported
    x6  2014  (current) supported

