#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright � 2016-2017, Okta, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# example scim messages
# https://support.okta.com/help/s/article/80110523-Provisioning-SCIM-Messages-Sent-by-Okta-to-a-SCIM-Server


from flask import Flask
from flask import request
from flask import url_for
from flask_socketio import SocketIO
from flask_socketio import emit
import flask
import logging
import warnings
import configparser
import sys
import base64
import json
import re
import traceback
warnings.filterwarnings("ignore")


config = configparser.ConfigParser()
config.read('config.ini')


appSchema = config.get('Okta', 'schema')

dbHost = config.get('Database', 'host')
dbPort = int(config.get('Database', 'port'))
dbUsername = config.get('Database', 'username')
dbPassword = config.get('Database', 'password')
dbService = config.get('Database', 'service')
dbQuery = config.get('Database', 'query')

authType = config.get('Auth', 'authType')
headerName = config.get('Auth', 'headerName')
headerValue = config.get('Auth', 'headerValue')


logging.basicConfig(level=logging.DEBUG, format='"%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"', datefmt='%m/%d/%Y %I:%M:%S %p', filename='scim.log')

application = Flask(__name__)
socketio = SocketIO(application)

testUser = {
    "userName": "test.user@test.com",
    "active": "true",
    "name": {
        "givenName": "Test",
        "middleName": "",
        "familyName": "User"
    },
    "emails": [
                {
                    "primary": True,
                    "value": "test@test1.com",
                    "type": "primary"
                },
                {
                    "primary": False,
                    "value": "test@test.com",
                    "type": "secondary"
                }
    ]
}


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
        self.userStatus = ""
        self.password = ""
        self.custom_attributes = {
            "title": ""
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
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User", "urn:okta:%s:1.0:user:custom" % appSchema, "urn:scim:schemas:core:1.0"],
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
        return rv



def scim_error(message, status_code=500):
    rv = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": message,
        "status": str(status_code)
    }
    return flask.jsonify(rv), status_code


def send_to_browser(obj):
    socketio.emit('user',
                  {'data': obj},
                  broadcast=True,
                  namespace='/test')


def render_json(obj):
    rv = obj.to_scim_resource()
    send_to_browser(rv)
    return flask.jsonify(rv)


@application.route('/')
def hello():
    return "This is a SCIM server"


@application.route('/scim/v2')
def base():
    return "This is a SCIM server"


@application.route("/scim/v2/Users", methods=['GET'])
def users_get():
    try:
        logging.info("Hitting GET endpoint, will return default user")
        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)
        # These lines are useful if we ever want to do logic on the GET call
        args = request.args
        search = args['filter']
        value = search.split('"')[1]
        logging.debug("Args: %s" % str(args))
        logging.debug("Username: %s" % value)
        test_user = User(testUser)
        test_user.id = value
        # for update tests
        # every call should be considered an update
        rv = ListResponse([test_user], start_index=1, count=None, total_results=1)
        # for creation tests
        # rv = ListResponse([])
        resp = flask.jsonify(rv.to_scim_resource())
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)



@application.route("/scim/v2/Users/<user_id>", methods=['GET'])
def user_get(user_id):
    return scim_error("Not Implemented")


# create user
# this will never be hit with the current configuration
@application.route("/scim/v2/Users", methods=['POST'])
def users_post():
    try:
        logging.info("Hitting the POST endpoint")
        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)
        user_resource = request.get_json(force=True)
        try:
            logging.debug("POST data received: " + str(user_resource))
        except UnicodeEncodeError:
            logging.debug("Could not log POST data due to unicode issue")
        user = User(user_resource)
        rv = user.to_scim_resource()
        logging.debug("Response to Okta: " + str(rv))
        resp = flask.jsonify(user_resource)
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


# update user
# delete user
@application.route("/scim/v2/Users/<user_id>", methods=['PUT'])
def users_put(user_id):
    try:
        logging.info("Hitting the PUT endpoint")
        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)
        user_resource = request.get_json(force=True)
        try:
            logging.debug("PUT data received: " + str(user_resource))
        except UnicodeEncodeError:
            logging.debug("Could not log PUT data due to unicode issue")
        user = User(user_resource)
        if user.password != "":
            logging.debug("New Password is: %s" % user.password)
        rv = user.to_scim_resource()
        logging.debug("Response to Okta: " + str(rv))
        resp = flask.jsonify(user_resource)
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


@application.route("/scim/v2/Users/<user_id>", methods=['PATCH'])
def users_patch(user_id):
    try:
        logging.info("Hitting the PATCH endpoint")
        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)
        user_resource = request.get_json(force=True)
        try:
            logging.debug("PATCH data received: " + str(user_resource))
        except UnicodeEncodeError:
            logging.debug("Could not log PATCH data due to unicode issue")
        user = User(user_resource)
        rv = user.to_scim_resource()
        logging.debug("Response to Okta: " + str(rv))
        resp = flask.jsonify(user_resource)
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


@application.route("/scim/v2/Groups", methods=['GET'])
def groups_get():
    rv = ListResponse([])
    return flask.jsonify(rv.to_scim_resource())


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
            "supported": True
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
                "PUSH_NEW_USERS",
                "PUSH_PASSWORD_UPDATES",
                "PUSH_PENDING_USERS",
                "PUSH_PROFILE_UPDATES",
                "PUSH_USER_DEACTIVATION",
                "REACTIVATE_USERS",
                "GROUP_PUSH"
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


if __name__ == "__main__":

    logging.info("Server attempting to start")
    #socketio.run(app, ssl_context=('cert.pem', 'key.pem'))
    socketio.run(application)
