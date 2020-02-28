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
import base64
import traceback
import mysql.connector
warnings.filterwarnings("ignore")


config = configparser.ConfigParser()
config.read('config.ini')


appSchema = config.get('Okta', 'schema')

dbHost = config.get('Database', 'host')
dbUsername = config.get('Database', 'username')
dbPassword = config.get('Database', 'password')
dbName = config.get('Database', 'database')

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


class Database:
    def __init__(self, host, user, psw, db):
        self.conn = mysql.connector.connect(
            host = host,
            user = user,
            passwd = psw,
            database = db
        )

    def query(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = []
        row = ()
        while row is not None:
            try:
                row = cursor.fetchone()
                results.append(row)
            except ValueError as e:
                row = ()
                # logging.debug("There was a value error thrown: %s" % e)
        results = list(filter(None, results))
        cursor.close()
        return results

    # note we are doing a case sensitive lookup on the email field
    def user_exists(self, username):
        user_result = self.query("SELECT email FROM users WHERE email = '%s'" % username)
        if len(user_result) == 1:
            return True
        else:
            return False

    def create_user(self, email, first_name, last_name, phone, password, active):
        statement = "INSERT INTO users (email, firstName, lastName, phone, password, active) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (email, first_name, last_name, phone, password, active)
        cursor = self.conn.cursor()
        cursor.execute(statement)
        self.conn.commit()

    def update_user(self, email, first_name, last_name, phone):
        statement = "UPDATE users SET email = '%s', firstName = '%s', lastName = '%s', phone = '%s' WHERE email = '%s'" % (email, first_name, last_name, phone, email)
        cursor = self.conn.cursor()
        cursor.execute(statement)
        self.conn.commit()

    def enable_user(self, email):
        statement = "UPDATE users SET active = 'True' WHERE email = '%s'" % email
        cursor = self.conn.cursor()
        cursor.execute(statement)
        self.conn.commit()

    def disable_user(self, email):
        statement = "UPDATE users SET active = 'False' WHERE email = '%s'" % email
        cursor = self.conn.cursor()
        cursor.execute(statement)
        self.conn.commit()

    def reset_password(self, email, password):
        statement = "UPDATE users SET password = '%s' WHERE email = '%s'" % (password, email)
        cursor = self.conn.cursor()
        cursor.execute(statement)
        self.conn.commit()

    def close_conn(self):
        self.conn.close()


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


@application.route("/scim/v2/Users/<user_id>", methods=['GET'])
def user_get(user_id):
    try:
        logging.info("Hitting /scim/v2/Users/<user_id> GET endpoint to validate the user was created properly")
        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)
        # Get the username from the request

        username = user_id
        logging.debug("Username: %s" % username)

        logging.debug("Initializing database")
        db = Database(dbHost, dbUsername, dbPassword, dbName)
        logging.debug("Looking for user in the database by username/email")
        # recall we will be assuming the email and username are the same value as there is no username column in the db
        if db.user_exists(username):
            return_user = User(testUser)
            return_user.userName = username
            return_user.id = username
            rv = ListResponse([return_user], start_index=1, count=None, total_results=1)
        else:
            rv = ListResponse([])
        db.close_conn()
        resp = flask.jsonify(rv.to_scim_resource())
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)


@application.route("/scim/v2/Users", methods=['GET'])
def users_get():
    try:
        logging.info("Hitting /scim/v2/Users GET endpoint to check user existence")
        headers = request.headers
        if not authenticate(headers, type=authType):
            logging.error("The credentials supplied to the SCIM service are invalid")
            return scim_error("The credentials supplied to the SCIM service are invalid", 401)
        # Get the username from the request
        args = request.args
        search = args['filter']
        username = search.split('"')[1]
        logging.debug("Args: %s" % str(args))
        logging.debug("Username: %s" % username)

        logging.debug("Initializing database")
        db = Database(dbHost, dbUsername, dbPassword, dbName)
        logging.debug("Looking for user in the database by username/email")
        # recall we will be assuming the email and username are the same value as there is no username column in the db
        if db.user_exists(username):
            return_user = User(testUser)
            return_user.userName = username
            return_user.id = username
            rv = ListResponse([return_user], start_index=1, count=None, total_results=1)
        else:
            rv = ListResponse([])
        db.close_conn()
        resp = flask.jsonify(rv.to_scim_resource())
        return resp, 201
    except Exception as e:
        logging.error("An unexpected error has occured: %s" % e)
        logging.error("Stack Trace: %s" % traceback.format_exc())
        return scim_error("An unexpected error has occured: %s" % e, 500)
 

# create user
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

        logging.debug("Initializing database")
        db = Database(dbHost, dbUsername, dbPassword, dbName)
        logging.debug("Inserting user into the database")
        # note that when creating the user we do not get a password from okta, so this field will be an empty string
        db.create_user(user.userName, user.givenName, user.familyName, user.mobilePhone, user.password, user.active)

        db.close_conn()
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
            dict_resource = dict(user_resource)
            # need to remove passwords from the log statement if it is in the object
            if 'password' in dict_resource.keys():
                dict_resource.pop('password')
            logging.debug("PUT data received: " + str(dict_resource))
            # uncomment below line for password debugging purposes
            #logging.debug("PUT data received: " + user_resource)
        except UnicodeEncodeError:
            logging.debug("Could not log PUT data due to unicode issue")
        user = User(user_resource)
        logging.debug("Initializing database")
        db = Database(dbHost, dbUsername, dbPassword, dbName)

        # note in this case the db row could be updated with one function instead of 4, but we are using 4 to demo
        # how this would work in a more complicated environment
        if user.password != "":
            logging.debug("Resetting the users password")
            db.reset_password(user.userName, user.password)
        if user.active:
            logging.debug("Activating the user")
            db.enable_user(user.userName)
        else:
            logging.debug("Deactivating the user")
            db.disable_user(user.userName)
        logging.debug("Updating the user")
        db.update_user(user.userName, user.givenName, user.familyName, user.mobilePhone)

        db.close_conn()
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

"""
# this block is for the bug in the POST section where it doesnt read the returned id value
# we will do all the check existence -> create or update logic in this function
# if uncommenting this section the user GET section will need to be modified to return a default user
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
            dict_resource = dict(user_resource)
            # need to remove passwords from the log statement if it is in the object
            if 'password' in dict_resource.keys():
                dict_resource.pop('password')
            logging.debug("PUT data received: " + str(dict_resource))
            # uncomment below line for password debugging purposes
            #logging.debug("PUT data received: " + user_resource)
        except UnicodeEncodeError:
            logging.debug("Could not log PUT data due to unicode issue")
        user = User(user_resource)

        logging.debug("Initializing database")
        db = Database(dbHost, dbUsername, dbPassword, dbName)
        logging.debug("Looking for user in the database by username/email")
        if db.user_exists(user.userName):
            # note in this case the db row could be updated with one function instead of 4, but we are using 4 to demo
            # how this would work in a more complicated environment
            if user.password != "":
                logging.debug("Resetting the users password")
                db.reset_password(user.userName, user.password)
            if user.active:
                logging.debug("Activating the user")
                db.enable_user(user.userName)
            else:
                logging.debug("Deactivating the user")
                db.disable_user(user.userName)
            logging.debug("Updating the user")
            db.update_user(user.userName, user.givenName, user.familyName, user.mobilePhone)
        else:
            logging.debug("Inserting user into the database")
            # note that when creating the user we do not get a password from okta, so this field will be an empty string
            db.create_user(user.userName, user.givenName, user.familyName, user.mobilePhone, user.password, user.active)

        db.close_conn()
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
"""

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
