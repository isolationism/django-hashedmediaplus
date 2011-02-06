#!/usr/bin/env python

# Distutils is the default python packager utility.
#from distutils.core import setup

# Setuptools is a slightly nicer distribution utility that can create 'eggs'.
from setuptools import setup, find_packages

setup(
    name='django-hashedmediaplus',
    version='0.1',
    description='A fork of django-hashedmedia that uses a hashed media manifest file '\
        '(instead of relying solely on the cache implementation), and providing URL '\
        'rewriting of image media linked via CSS file to its hashed filename counterpart.',
    author='Kevin Williams',
    author_email='kevin@weblivion.com',
    url='http://www.weblivion.com/',
    packages=find_packages(),
    include_package_data = False,
    install_requires = ['django'],
)

