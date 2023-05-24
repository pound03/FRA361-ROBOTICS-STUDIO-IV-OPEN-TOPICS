from setuptools import find_packages
from setuptools import setup

setup(
    name='check_qos',
    version='0.0.0',
    packages=find_packages(
        include=('check_qos', 'check_qos.*')),
)
