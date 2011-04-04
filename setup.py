#!/usr/bin/env python

# Distutils is the default python packager utility.
#from distutils.core import setup

# Setuptools is a slightly nicer distribution utility that can create 'eggs'.
from setuptools import setup, find_packages

setup(
    name='django-hashedmediaplus',
    author='Kevin Williams',
    author_email='kevin@weblivion.com',
    version='0.1.2',
    license='BEER-WARE',
    url='https://github.com/isolationism/django-hashedmediaplus',
    download_url='https://github.com/isolationism/django-hashedmediaplus/tarball/master',
    description='A fork of django-hashedmedia with some performance and functional enhancements',
    packages=find_packages(),
    include_package_data = False,
    install_requires = ['django'],
)

