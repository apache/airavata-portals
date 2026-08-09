import os

from setuptools import find_packages, setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name="airavata_custos_portal",
    version="0.0.6",
    url="https://github.com/apache/airavata-custos-portal",
    author="Apache Software Foundation",
    author_email="dev@airavata.apache.org",
    description=(
        "The Airavata Custos Portal SDK is a library that makes "
        "it easier to develop Airavata Custos Portal customizations."
    ),
    long_description=read("README.md"),
    long_description_content_type='text/markdown',
    license="Apache License 2.0",
    packages=['airavata_custos_portal', 'airavata_custos_portal.apps', 'airavata_custos_portal.apps.frontend',
              'airavata_custos_portal.apps.api'],
    package_data={'airavata_custos_portal.apps.frontend': ['static/**/*', 'templates/**/*']},
    install_requires=[
        "Django<6.0",
        "django-webpack-loader",
        "djangorestframework",
        "requests",
        "PyJWT",
        "django-environ"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ]
)
