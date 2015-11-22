lsdreader
=========

python analog ABBYY DSL Compiler - decomile LSD dictionary to DSL.

Support X3 and X5 lsd files format.

Based on C++ source decoder.zip from ru-board user [tr7](http://forum.ru-board.com/profile.cgi?action=show&member=tr7) 
[Source on github](https://github.com/nongeneric/lsd2dsl)

Russian decompiling team on [ru-board.ru](http://forum.ru-board.com/topic.cgi?forum=93&topic=3774)

Install
-------
    easy_install lingvoreader-0.1.6-py2.7.egg

or

    pip install lingvoreader

Usage
-----
    usage: lsdreader [-h] [--header] (-i INPUT | -a) [-o OUTDIR] [-c] [-v] [--version]
    
    Decode Lingvo X3 and X5 lsd dictionary to dsl
    
    optional arguments:
      -h, --help            show this help message and exit
      --header               show header info and exit
      -i INPUT, --input INPUT
                            Dictionary to decode
      -a, --all             All dictionary in current directory
      -o OUTDIR, --outdir OUTDIR
                            Output directory
      -c, --codecs          print supported languages and their codes
      -v, --verbose
      --version             show program's version number and exit

Lingvo versions
---------------
    11  2005
    12  2006
    x3  2008  supported
    x5  2011  supported
    x6  2014  (current)

Prep distribution
---------------
make tar.gz for PyPi
    
    python setup.py sdist

Install development version

    pip install -e .
