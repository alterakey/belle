import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'SQLAlchemy',
    'PIL',
    'freetype-py'
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(
    name="belle",
    version='0.1.3',
    description="belle, renderer",
    long_description="""""",
    classifiers=[
      "Programming Language :: Python",
      "Programming Language :: Python :: 2.6",
      "Programming Language :: Python :: 2.7"
      ],
    keywords='',
    author="Takahiro Yoshimura",
    author_email="altakey@gmail.com",
    url="http://github.com/taky/belle",
    license='GPL',
    packages=find_packages(exclude=['tests']),
    install_requires = requires,
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    tests_require=['nose'],
    entry_points="""""",
)
