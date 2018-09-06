# pylint: disable=C0111
from os.path import join, dirname
from setuptools import setup

here = dirname(__file__)
about = {}
with open(join(here, 'spectrum_client', '__version__.py'), 'r') as fh:
    exec(fh.read(), about)

with open(join(here, 'README.md'), 'r') as fh:
    README = fh.read().strip()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=README,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    license=about['__license__'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring',
    ],
    keywords='spectrum-client network monitoring spectrum',
    packages=['spectrum_client'],
    setup_requires=['setuptools>=40.2.0'],
    install_requires=['requests'],
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    project_urls={
        'Bug Reports': 'https://github.com/orgito/spectrum-client/issues',
        'Source': 'https://github.com/orgito/spectrum-client',
    },
)
