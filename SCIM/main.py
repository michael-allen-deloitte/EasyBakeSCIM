# example scim messages
# https://support.okta.com/help/s/article/80110523-Provisioning-SCIM-Messages-Sent-by-Okta-to-a-SCIM-Server


from flask import Flask
from flask import request
from flask import url_for
from flask_socketio import SocketIO
import flask
import logging
import warnings
import configparser
import sys
import base64

warnings.filterwarnings("ignore")


config = configparser.ConfigParser()
config.read('config.ini')

appSchema = config.get('Okta', 'schema')

authType = config.get('Auth', 'authType')
headerName = config.get('Auth', 'headerName')
headerValue = config.get('Auth', 'headerValue')


logging.basicConfig(level=logging.DEBUG, format='"%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"', datefmt='%m/%d/%Y %I:%M:%S %p', stream=sys.stdout)

application = Flask(__name__)
socketio = SocketIO(application)


class ListResponse():
    def __init__(self, list, start_index=1, count=None, total_results=0):
        self.list = list
        self.start_index = start_index
        self.count = count
        self.total_results = total_results

    def to_scim_resource(self):
        logging.debug("converting ListResponse to SCIM object")
        rv = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": self.total_results,
            "startIndex": self.start_index,
            "Resources": []
        }
        resources = []
        for item in self.list:
            resources.append(item.to_scim_resource())
        if self.count:
            rv['itemsPerPage'] = self.count
        rv['Resources'] = resources
        return rv


class User():
    def __init__(self, resource):
        self.id = ""
        self.active = ""
        self.userName = ""
        self.familyName = ""
        self.middleName = ""
        self.givenName = ""
        self.email = ""
        self.secondaryEmail = ""
        # for this object we are assuming only one phone number and that it is always has type 'mobile'
        self.mobilePhone = ""
        self.password = ""
        # there are no custom attributes in this lab but we will leave this here as it does not impact anything else
        # and keeping it will make it easier to extend with a custom attribute in the future
        self.custom_attributes = {
            "placeholder": ""
        }
        self.update(resource)
        self.id = self.userName


    def update(self, resource):
        logging.debug("Updating user object with values from Okta")
        keys = dict(resource).keys()
        customKey = ""
        for key in keys:
            if "urn:okta:" in key:
                customKey = key
            # example phone number obj: 'phoneNumbers': [{'value': '123-654-4815', 'primary': True, 'type': 'mobile'}]
            if 'phoneNumbers' in key:
                for number in resource[key]:
                    if number['primary']:
                        self.mobilePhone = number['value']
        for attribute in ['userName', 'active', 'password']:
            if attribute in resource:
                setattr(self, attribute, resource[attribute])
        for attribute in ['givenName', 'middleName', 'familyName']:
            if attribute in resource['name']:
                setattr(self, attribute, resource['name'][attribute])
        try:
            for attribute in resource['emails']:
                if attribute['primary']:
                    self.email = attribute['value']
                else:
                    self.secondaryEmail = attribute['value']
        except KeyError:
            pass
        # get custom attributes
        try:
            for attribute in resource[customKey]:
                self.custom_attributes[attribute] = resource[customKey][attribute]
        except KeyError:
            pass


    def to_scim_resource(self):
        logging.debug("Converting User obj to SCIM resource")
        if self.secondaryEmail == "":
            emails = [
                {
                    "primary": True,
                    "value": self.email,
                    "type": "primary"
                }
            ]
        else:
            emails = [
                {
                    "primary": True,
                    "value": self.email,
                    "type": "primary"
                },
                {
                    "primary": False,
                    "value": self.secondaryEmail,
                    "type": "secondary"
                }
            ]
        rv = {
            "schemas": ["urn:scim:schemas:extension:enterprise:1.0", "urn:okta:%s:1.0:user:custom" % appSchema, "urn:scim:schemas:core:1.0"],
            "id": self.id,
            "userName": self.userName,
            "name": {
                "familyName": self.familyName,
                "givenName": self.givenName,
                "middleName": self.middleName,
            },
            "active": self.active,
            "meta": {
                "resourceType": "User",
                "location": url_for('user_get',
                                    user_id=self.id,
                                    _external=True)
                # "created": "2010-01-23T04:56:22Z",
                # "lastModified": "2011-05-13T04:42:34Z",
            },
            "emails": emails,
            "urn:okta:%s:1.0:user:custom" % appSchema: self.custom_attributes
        }
        if self.mobilePhone != "":
            phone_numbers = [
                {
                    "primary": True,
                    "value": self.mobilePhone,
                    "type": "mobile"
                }
            ]
            rv['phoneNumbers'] = phone_numbers
        return rv


@application.route("/scim/v2/ServiceProviderConfigs", methods=['GET'])
def sp_configs_get():
    logging.info("/scim/v2/ServiceProviderConfigs -- Checking available methods")
    headers = request.headers
    if not authenticate(headers, type=authType):
        logging.error("The credentials supplied to the SCIM service are invalid")
        return scim_error("The credentials supplied to the SCIM service are invalid", 401)
    supported_methods = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "patch": {
            "supported": True
        },
        "bulk": {
            "supported": True,
            "maxOperations": 1000,
            "maxPayloadSize": 1048576
        },
        "filter": {
            "supported": True,
            "maxResults": 200
        },
        "changePassword": {
            "supported": False
        },
        "sort": {
            "supported": True
        },
        "etag": {
            "supported": True
        },
        "authenticationSchemes": {
            "type": "httpbasic",
            "name": "HTTP Basic",
            "description": "Authentication scheme using the HTTP Basic Standard"
        },
        # possible values here: https://support.okta.com/help/s/article/30093436-Creating-SCIM-Connectors
        "urn:okta:schemas:scim:providerconfig:1.0": {
            "userManagementCapabilities": [
                "IMPORT_PROFILE_UPDATES",
                "IMPORT_NEW_USERS"
            ]
        }
    }
    return flask.jsonify(supported_methods)


def authenticate(headers, type='Header'):
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


def scim_error(message, status_code=500):
    rv = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": message,
        "status": str(status_code)
    }
    return flask.jsonify(rv), status_code


if __name__ == "__main__":

    logging.info("Server attempting to start")
    socketio.run(application)
