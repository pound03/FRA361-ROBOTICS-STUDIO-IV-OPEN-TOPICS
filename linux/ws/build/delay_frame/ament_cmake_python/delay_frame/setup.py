from setuptools import find_packages
from setuptools import setup

setup(
    name='delay_frame',
    version='0.0.0',
    packages=find_packages(
        include=('delay_frame', 'delay_frame.*')),
)
