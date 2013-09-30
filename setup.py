#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'svolkov'
from setuptools import setup, find_packages

setup(
    name="lingvoreader",
    version="0.1",
    author=__author__,
    author_email='sv99@inbox.ru',
    description='Lingvo X5 lsd reader Utilities',
    packages=find_packages(),
    platforms='any',
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'lsdreader = lingvoreader.lsdreader:main',
        ]
    }
)