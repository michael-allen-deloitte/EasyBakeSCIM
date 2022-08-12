import base64
import logging

from SCIM import config, LOG_LEVEL, LOG_FORMAT

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

headerName = config['Auth']['headerName']
headerValue = config['Auth']['headerValue']


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