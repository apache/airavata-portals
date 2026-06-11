import os

from setuptools import find_packages, setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='airavata-django-portal',
    version='0.1',
    url='https://github.com/apache/airavata-django-portal',
    author='Apache Software Foundation',
    author_email='dev@airavata.apache.org',
    description=('The Airavata Django Portal is a web interface to the '
                 'Apache Airavata API implemented using the Django web '
                 'framework.'),
    long_description=read('README.md'),
    license='Apache License 2.0',
    packages=find_packages(),
    install_requires=[
            'Django',
            'requests',
            'requests-oauthlib',
            'django-webpack-loader',
            'PyJWT',
            # Notebook output rendering (apps/api/output_views.py).
            'papermill',
            'nbconvert',
            # gRPC runtime for the Airavata SDK stubs.
            'grpcio>=1.60.0',
            'protobuf>=5.26.0,<7.0.0',
            'googleapis-common-protos>=1.62.0',
            # The gRPC Airavata SDK is the portal's sole Airavata dependency. It
            # is not yet on PyPI (the published 2.2.7 is the retired Thrift SDK),
            # so for development install it editable from a local apache/airavata
            # checkout: pip install -e <airavata>/airavata-python-sdk
            # The release version (2.2.8 / 2.3.0 / 3.x) is TBD; bump this pin with it.
            'airavata-python-sdk>=3.0.0',
    ],
    extras_require={
        'dev': [
            'flake8',
            'flake8-isort'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ]
)
