#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-01-04 15:16

@author: johannes
"""
import os
import setuptools


requirements = []
with open('requirements.txt', 'r') as fh:
    for line in fh:
        requirements.append(line.strip())

NAME = 'profileqc'
VERSION = '0.1.1'
README = open('READMEpypi.rst', 'r').read()

setuptools.setup(
    name=NAME,
    version=VERSION,
    author="Johannes Johansson",
    author_email="johannes.johansson@smhi.se",
    description="Package for quality control of high resolution profile data.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/sharksmhi/profileqc",
    packages=setuptools.find_packages(),
    package_data={
        'profileqc': [
            os.path.join('etc', '*.json'),
            os.path.join('etc', '*.yaml'),
            os.path.join('etc', 'qc_routines', '*.yaml'),
            os.path.join('etc', 'qc_advanced_spec', '*.xlsx'),
            os.path.join('etc', 'resources', 'shp', '*'),
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=requirements,
)
