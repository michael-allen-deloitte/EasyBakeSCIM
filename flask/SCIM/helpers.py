import base64
from linecache import cache
import os
import json
import platform
import time
from typing import Union, List

from SCIM import config

headerName = config['Auth']['headerName']
headerValue = config['Auth']['headerValue']

def creation_time(path_to_file) -> float:
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

class Cache:
    cache_base_dir = config['Cache']['dir']
    cache_lifetime_sec = int(config['Cache']['lifetime'])*60

    def __init__(self, file_name: str) -> None:
        if not os.path.exists(self.cache_base_dir):
            os.mkdir(self.cache_base_dir)
        self.cache_file_path = self.cache_base_dir.strip('/').strip('\\') + '/' + file_name
        # if there already exists a cache file on startup delete it
        if os.path.isfile(self.cache_file_path):
            os.remove(self.cache_file_path)

    def check_cache_lifetime_valid(self) -> bool:
        cache_created = creation_time(self.cache_file_path)
        return time.time() > cache_created + self.cache_lifetime_sec

    def write_json_cache(self, json_obj: dict) -> None:
        # if the cache already exists
        if os.path.isfile(self.cache_file_path):
            # if its no longer valid overwrite it
            # if it is valid do nothing
            if self.check_cache_lifetime_valid():
                os.remove(self.cache_file_path)
                cache_file = open(self.cache_file_path, 'w')
                json.dump(json_obj, cache_file)
                cache_file.close()
        # if not write it
        else:
            with open(self.cache_file_path, 'w') as cache_file:
                json.dump(json_obj, cache_file)
        
    
    def read_json_cache(self) -> Union[List[dict], dict]:
        if self.check_cache_lifetime_valid():
            with open(self.cache_file_path, 'r') as cache_file:
                return json.load(cache_file)
        else:
            raise TimeoutError('The cache has timed out')


def authenticate(headers, type='Header') -> bool:
    if type.lower() == 'header':
        try:
            return headers[headerName] == headerValue
        except:
            return False
    elif type.lower() == "basic":
        unpw = str(base64.b64decode(headers['Authorization'].split(' ')[1]))
        username = unpw.split(':')[0].replace("'", '')[1:]
        password = unpw.split(':')[1].replace("'", '')
        return username == headerName and password == headerValue
    else:
        raise ValueError("The authentication type: %s is not recognized" % type)


def scim_error(message, status_code=500, stack_trace:str = None) -> dict:
    rv = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": message,
        "status": status_code
    }
    if stack_trace is not None:
        rv['stack_trace'] = stack_trace
    return rv

def create_spconfig_json() -> dict:
    spconfig_json = {
        'schemas': ['urn:scim:schemas:core:1.0', 'urn:okta:schemas:scim:providerconfig:1.0'],
        'patch': {'supported': False},
        'bulk': {'supported': False},
        'sort': {'supported': False},
        'etag': {'supported': False},
        'filter': {'supported': True, 'maxResults': 200},
        'authenticationSchemes': []
    }
    possible_provisioning_features = config['SCIM Features'].keys()
    supported_provisioning_features = []
    for feature in possible_provisioning_features:
        if config['SCIM Features'][feature].lower() == 'true': supported_provisioning_features.append(feature.upper())
    spconfig_json['changePassword'] = {'supported': 'PUSH_PASSWORD_UPDATES' in supported_provisioning_features}
    spconfig_json['urn:okta:schemas:scim:providerconfig:1.0'] = {'userManagementCapabilities': supported_provisioning_features}
    return spconfig_json