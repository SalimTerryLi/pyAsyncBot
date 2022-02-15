#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='pyAsyncBot',
    packages=find_packages(include=['pyasyncbot', 'pyasyncbot.*']),
    version='0.4.0',
    description='An async chat bot client framework',
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
