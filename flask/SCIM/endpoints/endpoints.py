import logging
from traceback import format_exc
from flask import request, jsonify, make_response
from flask_restful import Resource

# import our specific class as a generic Backend name, so that only the class being imported needs to be modified and the rest of the code runs the same
# all specific implementations should be subclasses of the SCIM.classes.generic.Backend.UserBackend class
from SCIM.classes.implementation.database.DBBackend import DBBackend as Backend
from SCIM.classes.generic.SCIMUser import SCIMUser, obj_list_to_scim_json_list
from SCIM.classes.generic.ListResponse import ListResponse
from SCIM.classes.generic.Cache import Cache
from SCIM.helpers import scim_error, create_spconfig_json

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = logging.Formatter('%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

backend = Backend()
list_users_cache = Cache('list_users.json')

SPCONFIG_JSON = create_spconfig_json()

def handle_server_side_error(e: Exception):
    error_json = scim_error("An unexpected error has occured: %s" % e, 500, format_exc())
    error_response = make_response(error_json, 500)
    logger.error(error_json)
    return error_response


class ServiceProviderConfigSCIM(Resource):
    def get(self):
        try:
            response = jsonify(SPCONFIG_JSON)
            logger.debug('Response: %s' % response)
            return response
        except Exception as e:
            return handle_server_side_error(e)


class UsersSCIM(Resource):
    # retrieve users: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-users
    def get(self) -> dict:
        try:
            # get url parameters
            args = request.args
            if 'startIndex' in args: 
                startIndex = int(args.get('startIndex'))
            else:
                startIndex = 1
            first_page: bool = startIndex == 1
            # check if first page, if so, call DB and set cache
            if first_page:
                logger.info('First page, reading users from database')
                users = backend.list_users()
                list_users_cache.write_json_cache(obj_list_to_scim_json_list(users))
            # else just get the users from the cache
            else:
                logger.info('Not the first page, reading users from cache')
                try:
                    users = list_users_cache.read_json_cache()
                except TimeoutError:
                    logger.info('Pulling from DB and saving new cache')
                    users = users = backend.list_users()
                    list_users_cache.write_json_cache(obj_list_to_scim_json_list(users))

            if 'totalResults' in args: 
                totalResults = int(args.get('totalResults'))
            else:
                totalResults = len(users)

            if 'count' in args: 
                count = int(args.get('count'))
            else:
                count = SPCONFIG_JSON['filter']['maxResults']
            if totalResults < count:
                count = totalResults

            response = ListResponse(users[startIndex-1:startIndex-1+count], startIndex, count, totalResults).scim_resource
            logger.debug('Response: %s' % response)
            return response
        except Exception as e:
            return handle_server_side_error(e)

    # create user: https://developer.okta.com/docs/reference/scim/scim-20/#create-the-user
    def post(self):
        # get request JSON, error out if invalid
        try:
            scim_json = request.get_json(force=True)
        except Exception as e:
            return scim_error('Invalid JSON', 400)

        try:
            in_scim_user = SCIMUser(scim_json, init_type='scim')
            logger.debug('Input: %s' % in_scim_user.scim_resource)
            out_scim_user = backend.create_user(in_scim_user)
            response = jsonify(out_scim_user.scim_resource)
            logger.debug('Response: %s' % response)
            return make_response(response, 201)
        except Exception as e:
            return handle_server_side_error(e)


class UserSpecificSCIM(Resource):
    # get a specific user: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-a-specific-user
    def get(self, user_id: str):
        try:
            scim_user: SCIMUser = backend.get_user(user_id)
            if scim_user is not None:
                list_resp = ListResponse([scim_user], start_index=1, count=None, total_results=1)
            else:
                list_resp = ListResponse([])
            response = list_resp.scim_resource
            logger.debug('Response: %s' % response)
            return response
        except Exception as e:
            return handle_server_side_error(e)

    # update a specific user: https://developer.okta.com/docs/reference/scim/scim-20/#update-a-specific-user-put
    # this is also used for user deactivations in AIN apps
    def put(self, user_id: str):
        # get request JSON, error out if invalid
        try:
            scim_json = request.get_json(force=True)
        except Exception as e:
            return scim_error('Invalid JSON', 400)

        try:
            in_scim_user = SCIMUser(scim_json, init_type='scim')
            logger.debug('Input: %s' % in_scim_user.scim_resource)
            out_scim_user = backend.update_user(in_scim_user)
            response = jsonify(out_scim_user.scim_resource)
            logger.debug('Response: %s' % response)
            return response
        except Exception as e:
            return handle_server_side_error(e)

    # update a specific user (activate, deactivate, sync password): https://developer.okta.com/docs/reference/scim/scim-20/#update-a-specific-user-patch
    # note okta says this is currently only supported for OIN applications, so if we create this as an app wizard app all of these updates
    # will happen in the PUT operation
    # this is also used for user deactivation in OIN apps
    """
    def patch(self, user_id: str):
        try:
            
        except Exception as e:
            return handle_server_side_error(e)
    """

    # Okta's notes on user deletion: https://developer.okta.com/docs/concepts/scim/#delete-deprovision


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