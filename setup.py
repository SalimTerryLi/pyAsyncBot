#!/usr/bin/env python

from setuptools import find_packages, setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='pyAsyncBot',
    packages=find_packages(include=['pyasyncbot', 'pyasyncbot.*']),
    version='0.5.0',
    description='An async chat bot client framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='SalimTerryLi',
    license='MIT',
    install_requires=[
        'ujson>=5.1.0',
        'asyncio>=3.4.3',
        'aiohttp>=3.8.1',
        'aiofiles>=0.8.0',
        'loguru>=0.6.0',
    ],
    scripts=[
        './bin/pyasyncbotd'
    ],
)
