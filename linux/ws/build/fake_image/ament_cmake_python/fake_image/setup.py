from setuptools import find_packages
from setuptools import setup

setup(
    name='fake_image',
    version='0.0.0',
    packages=find_packages(
        include=('fake_image', 'fake_image.*')),
)
