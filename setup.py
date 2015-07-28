#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'sv99'
from setuptools import setup, find_packages

with open('README.txt') as file:
    readme_txt = file.read()

setup(
    name="lingvoreader",
    version="0.1.5",
    author=__author__,
    author_email='sv99@inbox.ru',
    url='https://github.com/sv99/lsdreader',
    description='Lingvo X5 lsd reader Utilities',
    long_description=readme_txt,
    packages=find_packages(),
    platforms='any',
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'lsdreader = lingvoreader.lsdreader:main',
        ]
    }
)