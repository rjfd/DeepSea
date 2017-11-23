# -*- coding: utf-8 -*-
import re
from setuptools import setup


def _get_deepsea_version():
    try:
        with open('version.txt', 'r') as f:
            return f.read()
    except IOError:
        return "(unknown-version)"

setup(
    name='deepsea',
    version=_get_deepsea_version(),
    package_dir={
        'deepsea': 'cli'
    },
    packages=['deepsea', 'deepsea.monitors'],
    entry_points={
        'console_scripts': [
            'deepsea = deepsea.__main__:main'
        ]
    },
    tests_require=['pytest']
)
