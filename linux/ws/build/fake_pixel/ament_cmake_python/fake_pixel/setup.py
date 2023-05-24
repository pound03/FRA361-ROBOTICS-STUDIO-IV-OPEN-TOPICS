from setuptools import find_packages
from setuptools import setup

setup(
    name='fake_pixel',
    version='0.0.0',
    packages=find_packages(
        include=('fake_pixel', 'fake_pixel.*')),
)
