# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name="tsuru-hcaas",
    version="0.1.0",
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
