from SCIM import app
from SCIM.helpers import authenticate, scim_error
from SCIM.classes import ListResponse, User
import flask
from flask import request
import logging
import configparser

logging.basicConfig(level=logging.DEBUG, format='"%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"', datefmt='%Y/%m/%d %I:%M:%S %p', filename='scim.log')

config = configparser.ConfigParser()
config.read('config.ini')

authType = config.get('Auth', 'authType')

@app.route('/', methods=['GET'])
def root():
    return "Hello World"

@app.route("/scim/v2/Users/<user_id>", methods=['GET'])
def user_get(user_id):
    return "Hello World"

# get users
@app.route("/scim/v2/Users", methods=['GET'])
def users_get():
    return "Hello World"

# create user
@app.route("/scim/v2/Users", methods=['POST'])
def users_post():
    return "Hello World"

# update user
# delete user
@app.route("/scim/v2/Users/<user_id>", methods=['PUT'])
def users_put(user_id):
    return "Hello World"

# capabilities definition route
@app.route("/scim/v2/ServiceProviderConfigs", methods=['GET'])
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