# pylint: disable=C0111
from setuptools import setup

with open("README.md", "r") as fh:
    README = fh.read()

setup(
    name='spectrum-client',
    version='0.0.5',
    description='CA Spectrum Web Services API wrapper',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Renato Orgito',
    author_email='orgito@gmail.com',
    maintainer='Renato Orgito',
    maintainer_email='orgito@gmail.com',
    url='https://github.com/orgito/spectrum-client',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring',
    ],
    keywords='spectrum-client network monitoring spectrum',
    packages=['spectrum_client'],
    setup_requires=['setuptools>=38.6.0'],
    install_requires=['requests'],
    python_requires='>=3.6',
    project_urls={
        'Bug Reports': 'https://github.com/orgito/spectrum-client/issues',
        'Source': 'https://github.com/orgito/spectrum-client',
    },
)
