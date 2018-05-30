import os

import requests
from requests.auth import HTTPBasicAuth

SPECTRUM_URL = os.environ.get('SPECTRUM_URL')
SPECTRUM_USERNAME = os.environ.get('SPECTRUM_USERNAME')
SPECTRUM_PASSWORD = os.environ.get('SPECTRUM_PASSSWORD')


class Spectrum(object):

    def __init__(self, url=SPECTRUM_URL, username=SPECTRUM_USERNAME, password=SPECTRUM_PASSWORD):
        if url is None:
            raise ValueError('Spectrum (OneClick) url must be provided either in the constructor or as an environment variable')
        self.url = url if not url.endswith('/') else url[:-1]
        self.auth = HTTPBasicAuth(username, password)

    def update_attribute(self, model_handle, attr_id, value):
        url = f'{self.url}/spectrum/restful/model/{model_handle}'
        params = {'attr': attr_id, 'val': value}
        res = requests.put(url, params=params, auth=self.auth)
        res.raise_for_status()
        return res.ok
