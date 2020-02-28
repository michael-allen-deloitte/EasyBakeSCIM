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
import traceback
import mysql.connector

warnings.filterwarnings("ignore")


config = configparser.ConfigParser()
config.read('config.ini')

appSchema = config.get('Okta', 'schema')

authType = config.get('Auth', 'authType')
headerName = config.get('Auth', 'headerName')
headerValue = config.get('Auth', 'headerValue')

dbHost = config.get('Database', 'host')
dbUser = config.get('Database', 'username')
dbPassword = config.get('Database', 'password')
dbDatabase = config.get('Database', 'database')


logging.basicConfig(level=logging.DEBUG, format='"%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"', datefmt='%m/%d/%Y %I:%M:%S %p', filename='scim.log')

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
        self.userStatus = ""
        self.custom_attributes = {
            "employee_number": ""
        }
        self.update(resource)


    def update(self, resource):
        self.id = resource[0]
        self.email = resource[1]
        self.userName = resource[1]
        self.givenName = resource[2]
        self.familyName = resource[3]
        self.custom_attributes['employee_number'] = resource[4]


    def to_scim_resource(self):
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
            "emails": emails,
            "urn:okta:%s:1.0:user:custom" % appSchema: self.custom_attributes
        }
        return rv


class Database:
    def __init__(self, host, user, psw, db):
        self.conn = mysql.connector.connect(
            host = host,
            user = user,
            passwd = psw,
            database = db
        )

    def query(self, statement):
        cursor = self.conn.cursor()
        cursor.execute(statement)
        result = cursor.fetchall()
        cursor.close()
        return result


@application.route("/scim/v2/Users", methods=['GET'])
def users_get():
    try:
        logging.info("Hitting GET endpoint")

        # get headers to validate authentication
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

        logging.debug('Reading users from the database')
        database = Database(dbHost, dbUser, dbPassword, dbDatabase)
        results = database.query('select * from users')
        logging.debug('Results returned from database: %i' % len(results))

        logging.debug('Converting database list to user objects')
        users = []
        for result in results:
            users.append(User(result))

        return_users = users[startIndex - 1: startIndex - 1 + count]

        logging.debug("Returning list response with parameters - startIndex: %s, count: %s, total_results: %s" % (str(startIndex), str(len(return_users)), str(len(users))))
        rv = ListResponse(return_users, start_index=startIndex, count=len(return_users), total_results=len(users))
        resp = flask.jsonify(rv.to_scim_resource())

        return resp, 201

    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)

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
