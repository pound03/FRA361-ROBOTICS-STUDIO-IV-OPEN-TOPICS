from setuptools import find_packages
from setuptools import setup

setup(
    name='pixel2coordinate',
    version='0.0.0',
    packages=find_packages(
        include=('pixel2coordinate', 'pixel2coordinate.*')),
)
