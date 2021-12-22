import flask
from flask_restful import Api
import logging

LOG_LEVEL = logging.INFO
LOG_FORMAT = logging.Formatter('%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')

app = flask.Flask(__name__)
api = Api(app)

from SCIM.endpoints import endpoints
api.add_resource(endpoints.UsersSCIM, '/scim/v2/Users')
api.add_resource(endpoints.UserSpecificSCIM, '/scim/v2/Users/<user_id>')
api.add_resource(endpoints.GroupsSCIM, '/scim/v2/Groups')
api.add_resource(endpoints.GroupsSpecificSCIM, '/scim/v2/Groups/<group_id>')