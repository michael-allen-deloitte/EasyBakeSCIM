import sys
from os import path
from base64 import b64decode
from typing import List, Literal
from configparser import ConfigParser
from logging import StreamHandler, Logger, Handler, Formatter, getLogger, NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
from werkzeug.datastructures import Headers

# doing inital setup here not using the set_up_logger() function for code organization sake
# the function needs LOG_LEVEL to be set, but a logger is needed for the config reading before
# the LOG_LEVEL could be read from the config
start_level = DEBUG
LOG_FORMAT = Formatter('%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
logger = getLogger(__name__)
logger.setLevel(start_level)
stream_handler = StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

config = ConfigParser()
# this value is relative to the run.py file
config_path = './SCIM/config.ini'
if path.exists(config_path):
    config.read(config_path)
else:
    logger.error('Could not read config file from path %s' % config_path)
    sys.exit(1)

log_level_string = config['General']['log_level']

if log_level_string.lower() == 'notset':
    LOG_LEVEL = NOTSET
elif log_level_string.lower() == 'debug':
    LOG_LEVEL = DEBUG
elif log_level_string.lower() == 'info':
    LOG_LEVEL = INFO
elif log_level_string.lower() == 'warning':
    LOG_LEVEL = WARNING
elif log_level_string.lower() == 'error':
    LOG_LEVEL = ERROR
elif log_level_string.lower() == 'critical':
    LOG_LEVEL = CRITICAL
else:
    LOG_LEVEL = INFO

headerName = config['Auth']['headerName']
headerValue = config['Auth']['headerValue']

def set_up_logger(name: str, level=LOG_LEVEL, handlers: List[Handler] = [StreamHandler()]) -> Logger:
    logger = getLogger(name)
    logger.setLevel(level)
    for handler in handlers:
        handler.setFormatter(LOG_FORMAT)
        logger.addHandler(handler)
    return logger

def authenticate(headers: Headers, type: str='Header') -> bool:
    if type.lower() == 'header':
        try:
            # using .get() instead of accessing as a dictionary
            # key returns None if the key doesnt exist instead of
            # throwing a KeyError
            return headers.get(headerName) == headerValue
        except:
            return False
    elif type.lower() == "basic" and headers.get('Authorization') is not None:
        # usually Authorization header comes in the form: Authorization = Basic/Bearer <creds/token>
        unpw = str(b64decode(headers.get('Authorization').split(' ')[1]))
        username = unpw.split(':')[0].replace("'", '')[1:]
        password = unpw.split(':')[1].replace("'", '')
        return username == headerName and password == headerValue
    else:
        raise ValueError("The authentication type: %s is not recognized" % type)

def scim_error(message: str, status_code: int=500, stack_trace:str = None) -> dict:
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
    possible_provisioning_features = list(config['SCIM Features'].keys())
    # remove this feature as its not one of Okta's, it is used in _init__.py to determine
    # if the /Groups endpoint should be included with the user import features
    possible_provisioning_features.remove('IMPORT_GROUPS_WITH_USERS'.lower())
    supported_provisioning_features = []
    for feature in possible_provisioning_features:
        if config['SCIM Features'][feature].lower() == 'true': supported_provisioning_features.append(feature.upper())
    spconfig_json['changePassword'] = {'supported': 'PUSH_PASSWORD_UPDATES' in supported_provisioning_features}
    spconfig_json['urn:okta:schemas:scim:providerconfig:1.0'] = {'userManagementCapabilities': supported_provisioning_features}
    return spconfig_json

def parse_log_level_from_config(log_level_string: str) -> Literal:
    if log_level_string.lower() == 'notset':
        return NOTSET
    elif log_level_string.lower() == 'debug':
        return DEBUG
    elif log_level_string.lower() == 'info':
        return INFO
    elif log_level_string.lower() == 'warning':
        return WARNING
    elif log_level_string.lower() == 'error':
        return ERROR
    elif log_level_string.lower() == 'critical':
        return CRITICAL
    else:
        return INFO