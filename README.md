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

oc = Spectrum('http://oneclick.mydomain:8080', 'myuser', 'secret')

# Update a model attribute
oc.update_attribute(0x210afa, 0x10024, 'MySNMPSecret')

# Update multiple attributes
updates = [(0x11564, notes), (0x12db9, 'JKL002'), (0x1295d, False)]
oc.update_attributes(mh, updates)

# Get a list of devices by name (only from landscape 0xa00000)
oc.devices_by_name('^SW00', 0xa00000)

# Get a lis tof devices by specific attribute from all landscapes
return oc.devices_by_attr(0x12db9, 'XYZ001')

# Get a list of devices by multipe matchng filters
oc.devices_by_filters([(attr1, 'equals', value1), (attr2, 'has-pcre', '^foo.*bar')], landscape)

# Put a model in maintenance mode
oc.set_maintenance(model_handle, True)

# Remove a model from maintenance mode
oc.set_maintenance(model_handle, False)
```

If not provided, server and credentials will be read from the environment variables `SPECTRUM_URL`, `SPECTRUM_USERNAME`, `SPECTRUM_PASSWORD`.