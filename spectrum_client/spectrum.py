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
    xml_namespace = {'ca': 'http://www.ca.com/spectrum/restful/schema/response'}
    default_attributes = '''
    <rs:requested-attribute id="0x1006e"/> <!-- Model Name -->
    <rs:requested-attribute id="0x1000a"/> <!-- Condition -->
    <rs:requested-attribute id="0x11ee8"/> <!-- Model Class -->
    <rs:requested-attribute id="0x129e7"/> <!-- Site ID -->
    <rs:requested-attribute id="0x12d7f"/> <!-- IP Address -->
    <rs:requested-attribute id="0x1290c"/> <!-- Criticality -->
    <rs:requested-attribute id="0x10000"/> <!-- Model Type Name -->
    <rs:requested-attribute id="0x23000e"/> <!-- Device Type -->
    <rs:requested-attribute id="0x11d42"/> <!-- Landscape Name-->
    <rs:requested-attribute id="0x1295d"/> <!-- isManaged-->
    <rs:requested-attribute id="0x11564"/> <!-- Notes-->
    <rs:requested-attribute id="0x12db9"/> <!-- ServiceDesk Asset ID-->
    '''
    models_search_template = '''<?xml version="1.0" encoding="UTF-8"?>
    <rs:model-request throttlesize="9999"
    xmlns:rs="http://www.ca.com/spectrum/restful/schema/request"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.ca.com/spectrum/restful/schema/request ../../../xsd/Request.xsd ">
        <rs:target-models>
            <rs:models-search>
                <rs:search-criteria xmlns="http://www.ca.com/spectrum/restful/schema/filter">
                    <filtered-models>
                    {models_filter}
                    </filtered-models>
                </rs:search-criteria>
            </rs:models-search>
        </rs:target-models>
    ''' + default_attributes + '</rs:model-request>'

    def __init__(self, url=SPECTRUM_URL, username=SPECTRUM_USERNAME, password=SPECTRUM_PASSWORD):
        if url is None:
            raise ValueError('Spectrum (OneClick) url must be provided either in the constructor or as an environment variable')
        self.url = url if not url.endswith('/') else url[:-1]
        self.auth = HTTPBasicAuth(username, password)

    def _parse_get(self, res):
        self.check_http_response(res)

        root = ET.fromstring(res.content)
        model_error = root.find('.//ca:model', self.xml_namespace).get('error')
        if model_error:
            raise SpectrumClientParameterError('Model Error: ' + model_error)
        attr_error = root.find('.//ca:attribute', self.xml_namespace).get('error')
        if attr_error:
            raise SpectrumClientParameterError(attr_error)

    def _parse_update(self, res):
        self.check_http_response(res)

        root = ET.fromstring(res.content)
        if root.find('.//ca:model', self.xml_namespace).get('error') == 'Success':
            return

        if root.find('.//ca:model', self.xml_namespace).get('error') == 'PartialFailure':
            msg = root.find('.//ca:attribute', self.xml_namespace).get('error-message')
        else:
            msg = root.find('.//ca:model', self.xml_namespace).get('error-message')
        raise SpectrumClientParameterError(msg)

    @staticmethod
    def check_http_response(res):
        if res.status_code == 401:
            raise SpectrumClientAuthException('Authorization Failure. Invalid user name or password.')
        res.raise_for_status()

    @staticmethod
    def xml_landscape_filter(landscape):
        xml = '''
        <greater-than>
            <attribute id="0x129fa">
                <value>{}</value>
            </attribute>
        </greater-than>
        <less-than>
            <attribute id="0x129fa">
                <value>{}</value>
            </attribute>
        </less-than>'''
        landscape_start = hex(landscape)
        landscape_end = hex(landscape + 0xfffff)
        return xml.format(landscape_start, landscape_end).strip()

    def get_attribute(self, model_handle, attr_id):
        """Get an attribute of a Spectrum model.

        Arguments:
            model_handle {int} -- Model Handle of the model being queried.
            attr_id {int} -- Attribute ID of the attribute being queried.
        """
        url = '{}/spectrum/restful/model/{}'.format(self.url, hex(model_handle))
        params = {'attr': hex(attr_id)}
        res = requests.get(url, params=params, auth=self.auth)
        self._parse_get(res)
        root = ET.fromstring(res.content)
        return root.find('.//ca:attribute', self.xml_namespace).text

    def devices_by_filters(self, filters, landscape=None):
        if isinstance(filters[0], (str, int)):
            filters = [filters]
        filters = [
            dict(
                operation=f[1],
                attr_id=hex(f[0]) if isinstance(f[0], int) else f[0],
                value=f[2]
            ) for f in filters
        ]
        filters = ['''
            <{operation}>
                <attribute id="{attr_id}">
                    <value>{value}</value>
                </attribute>
            </{operation}>'''.format(**f) for f in filters
        ]
        filters = '\n'.join(filters)
        if landscape:
            landscape_filter = self.xml_landscape_filter(landscape)
        else:
            landscape_filter = ''

        models_filter = '''
        <and>
            <is-derived-from>
                <model-type>0x1004b</model-type> <!-- Device -->
            </is-derived-from>
            {landscape_filter}
            {filters}
         </and>'''.format(landscape_filter=landscape_filter, filters=filters)
        xml = self.models_search_template.format(models_filter=models_filter)
        return self.search_models(xml)

    def devices_by_attr(self, attr, value, landscape=None):
        return self.devices_by_filters([(attr, 'equals', value)], landscape)

    def devices_by_name(self, regex, landscape=None):
        return self.devices_by_filters([('0x1006e', 'has-pcre', regex)], landscape)

    def search_models(self, xml):
        url = '{}/spectrum/restful/models'.format(self.url)
        res = requests.post(url, xml, auth=self.auth)
        self.check_http_response(res)
        root = ET.fromstring(res.content)
        etmodels = root.findall('.//ca:model', self.xml_namespace)
        models = {
            model.get('mh'): {
                attr.get('id'): attr.text for attr in model.getchildren()
            } for model in etmodels
        }
        return models

    def set_maintenance(self, model_handle, on=True):
        return self.update_attribute(model_handle, 0x1295d, str(not on))

    def update_attribute(self, model_handle, attr_id, value):
        self.update_attributes(model_handle, (attr_id, value))

    def update_attributes(self, model_handle, updates):
        if isinstance(model_handle, int):
            model_handle = hex(model_handle)
        if isinstance(updates[0], (str, int)):
            updates = [updates]
        updates = [
            f(x) for x in updates for f in (
                lambda x: ('attr', hex(x[0]) if isinstance(x[0], int) else x[0]),
                lambda x: ('val', x[1])
            )
        ]
        url = self.url + '/spectrum/restful/model/{}'.format(model_handle)
        res = requests.put(url, params=updates, auth=self.auth)
        self._parse_update(res)
