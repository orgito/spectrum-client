#!/bin/local/python3
"""specrum_client"""

import os
import xml.etree.ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth

SPECTRUM_URL = os.environ.get("SPECTRUM_URL")
SPECTRUM_USERNAME = os.environ.get("SPECTRUM_USERNAME")
SPECTRUM_PASSWORD = os.environ.get("SPECTRUM_PASSWORD")


class SpectrumClientException(Exception):
    """Raised on OneClick errors"""


class SpectrumClientAuthException(SpectrumClientException):
    """Raised on authentication errrors"""


class SpectrumClientParameterError(SpectrumClientException):
    """Raised when invalid parameters are passed"""


class Spectrum(object):
    """A wrapper form OneClick REST API."""
    headers = {"Content-Type": "application/xml"}

    xml_namespace = {"ca": "http://www.ca.com/spectrum/restful/schema/response"}
    default_attributes = """
    <rs:requested-attribute id="0x129fa"/> <!-- Model Handle -->
    <rs:requested-attribute id="0x1006e"/> <!-- Model Name -->
    <rs:requested-attribute id="0x1000a"/> <!-- Condition -->
    <rs:requested-attribute id="0x11ee8"/> <!-- Model Class -->
    <rs:requested-attribute id="0x129e7"/> <!-- Site ID -->
    <rs:requested-attribute id="0x12d7f"/> <!-- IP Address -->
    <rs:requested-attribute id="0x1290c"/> <!-- Criticality -->
    <rs:requested-attribute id="0x10000"/> <!-- Model Type Name -->
    <rs:requested-attribute id="0x10001"/> <!-- Model Type Handle -->
    <rs:requested-attribute id="0x23000e"/> <!-- Device Type -->
    <rs:requested-attribute id="0x11d42"/> <!-- Landscape Name-->
    <rs:requested-attribute id="0x1295d"/> <!-- isManaged-->
    <rs:requested-attribute id="0x11564"/> <!-- Notes-->
    <rs:requested-attribute id="0x12db9"/> <!-- ServiceDesk Asset ID-->
    """
    models_search_template = """<?xml version="1.0" encoding="UTF-8"?>
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
    """ + default_attributes + "</rs:model-request>"

    event_by_ip_template = """<?xml version="1.0" encoding="UTF-8"?>
    <rs:event-request throttlesize="10" xmlns:rs="http://www.ca.com/spectrum/restful/schema/request" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.ca.com/spectrum/restful/schema/request ../../../xsd/Request.xsd">
        <rs:event>
            <rs:target-models>
                <rs:models-search>
                    <rs:search-criteria xmlns="http://www.ca.com/spectrum/restful/schema/filter">
                    <action-models>
                        <filtered-models>
                        <equals>
                            <model-type>SearchManager</model-type>
                        </equals>
                        </filtered-models>
                        <action>FIND_DEV_MODELS_BY_IP</action>
                        <attribute id="AttributeID.NETWORK_ADDRESS">
                            <value>{address}</value>
                        </attribute>
                    </action-models>
                    </rs:search-criteria>
                </rs:models-search>
            </rs:target-models>
            <!-- event ID -->
            <rs:event-type id="{event}"/>
            <!-- attributes/varbinds -->
            {var_binds}
        </rs:event>
    </rs:event-request>
"""

    def __init__(self, url=SPECTRUM_URL, username=SPECTRUM_USERNAME, password=SPECTRUM_PASSWORD):
        if url is None:
            raise ValueError("Spectrum (OneClick) url must be provided either in the constructor or as an environment variable")
        self.url = url if not url.endswith("/") else url[:-1]
        self.auth = HTTPBasicAuth(username, password)

    def _parse_get(self, res):
        self._check_http_response(res)

        root = ET.fromstring(res.content)
        try:
            model_error = root.find(".//ca:model", self.xml_namespace).get("error")
            if model_error:
                raise SpectrumClientParameterError("Model Error: " + model_error)
        except AttributeError:
            pass

        try:
            attr_error = root.find(".//ca:attribute", self.xml_namespace).get("error")
            if attr_error:
                raise SpectrumClientParameterError(attr_error)
        except AttributeError:
            pass

        try:
            list_error = root.find(".//ca:attribute-list", self.xml_namespace).get("error")
            if list_error:
                raise SpectrumClientParameterError(list_error)
        except AttributeError:
            pass
        
        try:
            responses_error = root.find(".//ca:model-responses", self.xml_namespace).get("error")
            if responses_error:
                raise SpectrumClientParameterError("Responses Error: " + responses_error)
        except AttributeError:
            pass

    def _parse_update(self, res):
        self._check_http_response(res)

        root = ET.fromstring(res.content)
        if root.find(".//ca:model", self.xml_namespace).get("error") == "Success":
            return

        if root.find(".//ca:model", self.xml_namespace).get("error") == "PartialFailure":
            msg = root.find(".//ca:attribute", self.xml_namespace).get("error-message")
        else:
            msg = root.find(".//ca:model", self.xml_namespace).get("error-message")
        raise SpectrumClientParameterError(msg)

    def _build_filter(self, filters, landscape=None):
        if isinstance(filters[0], (str, int)):
            filters = [filters]
        filters = [
            dict(
                operation=f[1],
                attr_id=hex(f[0]) if isinstance(f[0], int) else f[0],
                value=f[2]
            ) for f in filters
        ]
        filters = ["""
            <{operation}>
                <attribute id="{attr_id}">
                    <value>{value}</value>
                </attribute>
            </{operation}>""".format(**f) for f in filters]
        filters = "\n".join(filters)
        if landscape:
            landscape_filter = self.xml_landscape_filter(landscape)
        else:
            landscape_filter = ""

        models_filter = f"""
        <and>
            {landscape_filter}
            {filters}
         </and>"""
        return(self.models_search_template.format(models_filter=models_filter))

    @staticmethod
    def _check_http_response(res):
        """Validate the HTTP response"""
        if res.status_code == 401:
            raise SpectrumClientAuthException("Authorization Failure. Invalid user name or password.")
        res.raise_for_status()

    @staticmethod
    def xml_landscape_filter(landscape):
        """Return a xml fragment filtering by landscape"""
        xml = """
        <greater-than>
            <attribute id="0x129fa">
                <value>{}</value>
            </attribute>
        </greater-than>
        <less-than>
            <attribute id="0x129fa">
                <value>{}</value>
            </attribute>
        </less-than>"""
        landscape_start = hex(landscape)
        landscape_end = hex(landscape + 0xfffff)
        return xml.format(landscape_start, landscape_end).strip()

    def get_attribute(self, model_handle, attr_id):
        """Get an attribute from Spectrum model.
        Arguments:
            model_handle {int} -- Model Handle of the model being queried.
            attr_id {int} -- Attribute ID of the attribute being queried.
        """
        if isinstance(model_handle, int):
            model_handle = hex(model_handle)
        if isinstance(attr_id, int):
            attr_id = hex(attr_id)

        url = f"{self.url}/spectrum/restful/model/{model_handle}"
        params = {"attr": attr_id}
        res = requests.get(url, params=params, auth=self.auth)
        self._parse_get(res)
        root = ET.fromstring(res.content)

        try:
            return root.find(".//ca:model", self.xml_namespace)
        except:
            pass

        try:
            return root.find(".//ca:attribute", self.xml_namespace)
        except:
            pass

        try:
            return root.find(".//ca:attribute-list", self.xml_namespace)
        except:
            pass

    def devices_by_filters(self, filters, landscape=None):
        """Returns a list of devices matching the filters"""
        device_only = (0x10001, "is-derived-from", 0x1004b)
        filters = [device_only] + filters
        xml = self._build_filter(filters, landscape)
        return self.search_models(xml)

    def devices_by_attr(self, attr, value, landscape=None):
        """Returns a list of devices matching an attribute value"""
        return self.devices_by_filters([(attr, "equals", value)], landscape)

    def devices_by_name(self, regex, landscape=None):
        """Returns a list of devices for which the name matches a regex"""
        return self.devices_by_filters([("0x1006e", "has-pcre", regex)], landscape)

    def models_by_filters(self, filters, landscape=None):
        """Returns a list of models matching the filters"""
        xml = self._build_filter(filters, landscape)
        return self.search_models(xml)

    def models_by_attr(self, attr, value, landscape=None):
        """Returns a list of models matching an attribute value"""
        return self.models_by_filters([(attr, "equals", value)], landscape)

    def models_by_name(self, regex, landscape=None):
        """Returns a list of models for which the name matches a regex"""
        return self.models_by_filters([("0x1006e", "has-pcre", regex)], landscape)

    def search_models(self, xml):
        """Returns the models matching the xml search"""
        url = "{}/spectrum/restful/models".format(self.url)
        res = requests.post(url, xml, headers=self.headers, auth=self.auth)
        self._check_http_response(res)
        root = ET.fromstring(res.content)
        etmodels = root.findall(".//ca:model", self.xml_namespace)
        models = {
            model.get("mh"): {
                attr.get("id"): attr.text for attr in model.getchildren()
            } for model in etmodels
        }
        return models

    def set_maintenance(self, model_handle, on=True):
        """Puts a device in maintenance mode"""
        return self.update_attribute(model_handle, 0x1295d, str(not on))

    def update_attribute(self, model_handle, attr_id, value):
        """Update a single  attribute of a model"""
        self.update_attributes(model_handle, (attr_id, value))

    def update_attributes(self, model_handle, updates):
        """Update a list of attributes of a model"""
        if isinstance(model_handle, int):
            model_handle = hex(model_handle)
        if isinstance(updates[0], (str, int)):
            updates = [updates]
        updates = [
            f(x) for x in updates for f in (
                lambda x: ("attr", hex(x[0]) if isinstance(x[0], int) else x[0]),
                lambda x: ("val", x[1])
            )
        ]
        url = f"{self.url}/spectrum/restful/model/{model_handle}"
        res = requests.put(url, params=updates, auth=self.auth)
        self._parse_update(res)

    # TODO: Parse the response
    def generate_event_by_ip(self, event, address, variables):
        var_binds = ""
        for key, value in variables.items():
            var_binds += f"<rs:varbind id={key}>{value}</rs:varbind>"
        xml = self.event_by_ip_template.format(event=event, address=address, var_binds=var_binds)
        url = self.url + "/spectrum/restful/events"
        res = requests.post(url, xml, headers=self.headers, auth=self.auth)
        return res
