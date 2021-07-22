from SCIM import app
from SCIM.helpers import authenticate, scim_error
from SCIM.classes import ListResponse, User, Backend
import flask
from flask import request
import logging
import traceback
from SCIM.classes import ListResponse, User
import flask
from flask import request
import logging
import configparser

logging.basicConfig(level=logging.DEBUG, format='"%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"', datefmt='%Y/%m/%d %I:%M:%S %p', filename='scim.log')

config = configparser.ConfigParser()
config.read('config.ini')

authType = config.get('Auth', 'authType')
appSchema = config.get('Okta', 'schema')


# commenting the code structure on this basic function, will use this basic structure for all routes
@app.route('/', methods=['GET'])
def root():
    # using bad practices catch all try/except so that we can return any error that occurs to Okta
    # this will make the troubleshooting much easier from the Okta dashboard
    try:
        # log the route for troubleshooting
        # POST/PUT methods should also log body
        logging.info('GET /')

        # make sure the request is authenticated, currently we only do Header and Basic Auth
        # will want to upgrade to OAUTH eventually
        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)

        # initialize the backend
        backend = Backend.Backend()

        # perform CRUD operation using the backend object here

        # get response and convert to proper format
        #resp = flask.jsonify(rv.to_scim_resource())

        # return response to Okta
        #return resp, 201
        return 'Hello World'
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


# get specific user
@app.route("/scim/v2/Users/<user_id>", methods=['GET'])
def user_get(user_id):
    try:
        logging.info('GET /scim/v2/User/%s' % user_id)

        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)

        backend = Backend.Backend()
        logging.debug('Attempting to get the user from the backend')
        user = backend.get_user(user_id)
        if user is not None:
            rv = ListResponse.ListResponse([user], start_index=1, count=None, total_results=1)
        else:
            rv = ListResponse.ListResponse([])

        logging.debug('Response to Okta: %s' % str(rv))
        resp = flask.jsonify(rv.to_scim_resource())
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


@app.route('/', methods=['GET'])
def root():
    return "Hello World"


@app.route("/scim/v2/Users/<user_id>", methods=['GET'])
def user_get(user_id):
    return "Hello World"


# get users
@app.route("/scim/v2/Users", methods=['GET'])
def users_get():
    try:
        logging.info('GET /scim/v2/Uesrs')

        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)

        # get params for pagination
        params = request.args.to_dict()
        logging.info("url parameters received: %s" % str(params))
        try:
            startIndex = int(params['startIndex'])
            count = int(params['count'])
        except KeyError:
            startIndex = 1
            count = 200

        logging.debug('Attempting to get users from backend')
        backend = Backend.Backend()
        users = backend.get_all_users()
        logging.debug('Results returned from database: %i' % len(users))

        # due to pagination we dont return all the users at once
        return_users = users[startIndex - 1: startIndex - 1 + count]

        logging.debug("Returning list response with parameters - startIndex: %s, count: %s, total_results: %s" % (str(startIndex), str(len(return_users)), str(len(users))))
        rv = ListResponse.ListResponse(return_users, start_index=startIndex, count=len(return_users), total_results=len(users))
        resp = flask.jsonify(rv.to_scim_resource())

        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


# create user
@app.route("/scim/v2/Users", methods=['POST'])
def users_post():
    try:
        logging.info('POST /scim/v2/Users')

        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)

        user_resource = request.get_json(force=True)
        try:
            logging.debug("POST data received: " + str(user_resource))
        except UnicodeEncodeError:
            logging.debug("Could not log POST data due to unicode issue")

        user = User.User(user_resource, appSchema)
        logging.debug('Attempting to create the user')
        backend = Backend.Backend()
        backend.create_user(user)

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
@app.route("/scim/v2/Users/<user_id>", methods=['PUT'])
def users_put(user_id):
    try:
        logging.info('PUT /scim/v2/Users/%s' % user_id)

        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)

        user_resource = request.get_json(force=True)
        try:
            dict_resource = dict(user_resource)
            # need to remove passwords from the log statement if it is in the object
            if 'password' in dict_resource.keys():
                dict_resource.pop('password')
            logging.debug("PUT data received: " + str(dict_resource))
            # uncomment below line for password debugging purposes
            # logging.debug("PUT data received: " + user_resource)
        except UnicodeEncodeError:
            logging.debug("Could not log PUT data due to unicode issue")

        user = User.User(user_resource)
        backend = Backend.Backend()

        if user.password != "":
            logging.debug("Resetting the users password")
            backend.reset_password(user)
        if user.active:
            logging.debug("Activating the user")
            backend.enable_user(user)
        else:
            logging.debug("Deactivating the user")
            backend.disable_user(user)
        logging.debug("Updating the user")
        backend.update_user(user)

        rv = user.to_scim_resource()
        # again removing the password from the log statement if it is the response
        if 'password' in rv.keys():
            rv.pop('password')
        logging.debug("Response to Okta: " + str(rv))
        resp = flask.jsonify(user_resource)
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


# capabilities definition route
@app.route("/scim/v2/ServiceProviderConfigs", methods=['GET'])
def sp_configs_get():
    try:
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
                    "IMPORT_NEW_USERS",
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
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


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
