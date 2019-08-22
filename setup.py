#!/usr/bin/env python

from os.path import abspath, dirname, join
from setuptools import setup, find_packages

VERSION = '1.0.0'

setup(
    name             = 'robotframework-roborunner',
    version          = VERSION,
    description      = 'parameterization, parallel execution and log combining',
    author           = 'nick grout',
    author_email     = 'nick@plusqa.com',
    url              = 'https://github.com/PQALAB/roborunner',
    keywords         = 'robotframework testing testautomation parallel log',
    platforms        = 'any',
    install_requires = ['robotframework'],
    package_dir      = {'': 'src'},
    packages         = find_packages('src'),
    entry_points     = {'console_scripts': ['roborunner = roborunner.run:run']}
)
