# spectrum-client

[![image](https://img.shields.io/pypi/v/spectrum-client.svg?style=flat-square)](https://pypi.org/project/spectrum-client)
[![image](https://img.shields.io/pypi/pyversions/spectrum-client.svg?style=flat-square)](https://pypi.org/project/spectrum-client)
[![image](https://img.shields.io/pypi/l/spectrum-client.svg?style=flat-square)](https://pypi.org/project/spectrum-client)

---

CA Spectrum Web Services API wrapper

## Instalation
spectrum-client is distributed on PyPI and is available on Linux/macOS and Windows and supports Python 3.6+.

``` bash
$ pip install -U spectrum-client
```

## Usage

``` python
from spectrum_client import Spectrum

spectrum = Spectrum('htt://oneclick.mydomain:8080', 'myuser', 'secret')

# Update a model attribute
spectrum.udpate_attribute(0x2760df,0x12bfc,'12345')
```