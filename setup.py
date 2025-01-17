#!/usr/bin/env python

import setuptools
import os.path
import sys
import codecs

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here,rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

if __name__ == "__main__":
    here = os.path.abspath(os.path.dirname(__file__))

    setuptools.setup(
        name="searcch-importer",
        version=get_version("src/searcch/importer/__init__.py"),
        author="David M Johnson",
        author_email="johnsond@flux.utah.edu",
        url="https://gitlab.flux.utah.edu/searcch/importer",
        description="A Python library, client, and server that imports and updates SEARCCH artifacts.",
        long_description="",
        # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Other Environment",
            "Intended Audience :: Developers",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Topic :: Utilities",
            "License :: OSI Approved :: GNU General Public License v3",
        ],
        keywords="searcch",
        package_dir={"":"src"},
        packages=setuptools.find_packages(where="src"),
        entry_points={
            "console_scripts": [
                "searcch-importer=searcch.importer.client.__main__:client_main"
            ],
        },
        package_data={
            "searcch": [
                "importer/db/migration/alembic.ini"
            ]
        },
        exclude_package_data={ "": [ ".git*" ] }
    )
