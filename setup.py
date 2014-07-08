# -*- coding: utf-8 -*-

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from setuptools import setup, find_packages

from healthcheck import __version__


setup(
    name="tsuru-hcaas",
    version=__version__,
    description="Healthcheck as a service API for Tsuru PaaS",
    author="Tsuru",
    author_email="tsuru@corp.globo.com",
    classifiers=[
        "Programming Language :: Python :: 2.7",
    ],
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=["Flask==0.10.1", "pyzabbix==0.6", "pymongo==2.6.3"],
)
