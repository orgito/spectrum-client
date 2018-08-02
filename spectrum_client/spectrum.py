import os
import xml.etree.ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth

SPECTRUM_URL = os.environ.get('SPECTRUM_URL')
SPECTRUM_USERNAME = os.environ.get('SPECTRUM_USERNAME')
SPECTRUM_PASSWORD = os.environ.get('SPECTRUM_PASSWORD')


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

    def _check_http(self, res):
        if res.status_code == 401:
            raise SpectrumClientAuthException('Authorization Failure. Invalid user name or password.')
        res.raise_for_status()

    def _parse_get(self, res):
        self._check_http(res)

        root = ET.fromstring(res.text)
        model_error = root.find('.//ca:model', self._namespace).get('error')
        if model_error:
            raise SpectrumClientParameterError('Model Error: ' + model_error)
        attr_error = root.find('.//ca:attribute', self._namespace).get('error')
        if attr_error:
            raise SpectrumClientParameterError(attr_error)

    def _parse_update(self, res):
        self._check_http(res)

        root = ET.fromstring(res.text)
        if root.find('.//ca:model', self._namespace).get('error') == 'Success':
            return

        if root.find('.//ca:model', self._namespace).get('error') == 'PartialFailure':
            msg = root.find('.//ca:attribute', self._namespace).get('error-message')
        else:
            msg = root.find('.//ca:model', self._namespace).get('error-message')
        raise SpectrumClientParameterError(msg)

    def get_attribute(self, model_handle, attr_id):
        """Get an attribute of a Spectrum model.

        Arguments:
            model_handle {int} -- Model Handle of the model being queried.
            attr_id {int} -- Attribute ID of the attribute being queried.
        """
        url = f'{self.url}/spectrum/restful/model/{hex(model_handle)}'
        params = {'attr': hex(attr_id)}
        res = requests.get(url, params=params, auth=self.auth)
        self._parse_get(res)
        root = ET.fromstring(res.text)
        return root.find('.//ca:attribute', self._namespace).text

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
        self._parse_update(res)

    def set_maintenance(self, model_handle, on=True):
        return self.update_attribute(model_handle, 0x1295d, str(not on))
