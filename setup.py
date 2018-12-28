#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import os
import re

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="lingvoreader",
    version=find_version("lingvoreader", "__init__.py"),
    author='sv99',
    author_email='sv99@inbox.ru',
    url='https://github.com/sv99/lsdreader',
    description='Linvo 11, 12, X3, X5 and X6 lsd reader Utilities\n compatible with python2.7 and python3',
    long_description=read('README.rst'),
    packages=find_packages(),
    platforms='any',
    install_requires=[
        'future; python_version == "2.7"',
    ],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'lsdreader = lingvoreader.lsdreader:main',
        ]
    }
)