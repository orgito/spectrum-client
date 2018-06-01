import os
import xml.etree.ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth

SPECTRUM_URL = os.environ.get('SPECTRUM_URL')
SPECTRUM_USERNAME = os.environ.get('SPECTRUM_USERNAME')
SPECTRUM_PASSWORD = os.environ.get('SPECTRUM_PASSSWORD')


class SpectrumClientException(Exception):
    pass


class SpectrumClientAuthException(SpectrumClientException):
    pass


class SpectrumClientParameterError(SpectrumClientException):
    pass


class Spectrum(object):

    _namespace = {'ca': 'http://www.ca.com/spectrum/restful/schema/response'}

    def __init__(self, url=SPECTRUM_URL, username=SPECTRUM_USERNAME, password=SPECTRUM_PASSWORD):
        if url is None:
            raise ValueError('Spectrum (OneClick) url must be provided either in the constructor or as an environment variable')
        self.url = url if not url.endswith('/') else url[:-1]
        self.auth = HTTPBasicAuth(username, password)

    def _parse_res(self, res):
        if res.status_code == 401:
            raise SpectrumClientAuthException('Authorization Failure. Invalid user name or password.')

        root = ET.fromstring(res.text)
        if root.find('.//ca:model', self._namespace).get('error') == 'Success':
            return

        if root.find('.//ca:model', self._namespace).get('error') == 'PartialFailure':
            msg = root.find('.//ca:attribute', self._namespace).get('error-message')
        else:
            msg = root.find('.//ca:model', self._namespace).get('error-message')
        raise SpectrumClientParameterError(msg)

    def update_attribute(self, model_handle, attr_id, value):
        """Update an attribute of a Spectrum model.

        Arguments:
            model_handle {int} -- Model Handle of the model being updated.
            attr_id {int} -- Attribute ID of the attribute being updated.
            value {int or str} -- Value to set the attribute to.
        """

        url = f'{self.url}/spectrum/restful/model/{hex(model_handle)}'
        params = {'attr': hex(attr_id), 'val': value}
        res = requests.put(url, params=params, auth=self.auth)
        self._parse_res(res)
