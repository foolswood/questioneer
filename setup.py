#!/usr/bin/env python

from distutils.core import setup

setup(
    name='questioneer',
    version='1.0',
    description='Web based questionnaire',
    author='David Honour',
    author_email='david@foolswood.co.uk',
    url='https://www.github.com/foolswood/questioneer',
    packages=['questioneer'],
    install_requires=[
        'aiohttp',
        'pyyaml'
    ]
)
