# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='deepsea',
    version='@VERSION@',
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
