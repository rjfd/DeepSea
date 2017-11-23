# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys
from setuptools import setup


if '--set-version' in sys.argv:
    idx = sys.argv.index('--set-version')
    sys.argv.pop(idx)
    version = sys.argv.pop(idx)


setup(
    name='deepsea',
    version='@VERSION@' if not version else version,
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
