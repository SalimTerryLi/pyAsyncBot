#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='oicq_web',
    packages=find_packages(include=['oicq_web']),
    version='0.0.1',
    description='A python binding for oicq-webd',
    author='SalimTerryLi',
    license='MIT',
    install_requires=[
        'ujson>=5.1.0',
        'asyncio>=3.4.3',
        'aiohttp>=3.8.1',
        'aiofiles>=0.8.0',
    ],
)
