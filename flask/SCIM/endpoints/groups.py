import logging
from flask_restful import Resource

# import our specific class as a generic Backend name, so that only the class being imported needs to be modified and the rest of the code runs the same
# all specific implementations should be subclasses of the SCIM.classes.generic.Backend.UserBackend class
from SCIM.classes.implementation.database.DBBackend import DBBackend as Backend
from SCIM.endpoints.general import handle_server_side_error

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = logging.Formatter('%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

backend = Backend()

class GroupsSCIM(Resource):
    # retreive groups: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-groups
    def get(self) -> dict:
        try:
            pass
        except Exception as e:
            return handle_server_side_error(e)

    # create group: https://developer.okta.com/docs/reference/scim/scim-20/#create-groups
    def post(self):
        try:
            pass
        except Exception as e:
            return handle_server_side_error(e)


class GroupsSpecificSCIM(Resource):
    # retreive specific group: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-specific-groups
    def get(self, group_id: str):
        try:
            pass
        except Exception as e:
            return handle_server_side_error(e)

    # update group name: https://developer.okta.com/docs/reference/scim/scim-20/#update-a-specific-group-name
    # update group membership: https://developer.okta.com/docs/reference/scim/scim-20/#update-specific-group-membership
    # this is for AIW applications
    def put(self, group_id: str):
        try:
            pass
        except Exception as e:
            return handle_server_side_error(e)

    # update group name: https://developer.okta.com/docs/reference/scim/scim-20/#update-a-specific-group-name
    # update group membership: https://developer.okta.com/docs/reference/scim/scim-20/#update-specific-group-membership
    # this is for OIN applications
    def patch(self, group_id: str):
        try:
            pass
        except Exception as e:
            return handle_server_side_error(e)

    # delete group: https://developer.okta.com/docs/reference/scim/scim-20/#delete-a-specific-group
    def delete(self, group_id: str):
        try:
            pass
        except Exception as e:
            return handle_server_side_error(e)