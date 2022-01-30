#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='pyAsyncBot',
    packages=find_packages(include=['pyasyncbot']),
    version='0.0.2',
    description='An async chat bot design for python3',
    author='SalimTerryLi',
    license='MIT',
    install_requires=[
        'ujson>=5.1.0',
        'asyncio>=3.4.3',
        'aiohttp>=3.8.1',
        'aiofiles>=0.8.0',
    ],
)
