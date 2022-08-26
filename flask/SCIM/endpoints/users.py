import logging
from typing import List
from flask import request, jsonify, make_response, Response
from flask_restful import Resource
from itsdangerous import exc

from SCIM import SUPPORTED_PROVISIONING_FEATURES
# import our specific class as a generic Backend name, so that only the class being imported needs to be modified and the rest of the code runs the same
# all specific implementations should be subclasses of the SCIM.classes.generic.Backend.UserBackend class
from SCIM.classes.implementation.database.DBBackend import DBBackend as Backend
# do the same pattern for your custom filter implementation as Backend
# if using the generic Filter object still add the line like this:
# from SCIM.classes.generic.Filter import Filter as FilterImplementation
from SCIM.classes.implementation.filters.CustomFilter import CustomFilter as FilterImplementation
from SCIM.classes.generic.Filter import FilterValidationError
from SCIM.classes.generic.SCIMUser import SCIMUser, obj_list_to_scim_json_list
from SCIM.classes.generic.ListResponse import ListResponse
from SCIM.endpoints.general import handle_server_side_error, handle_validation_error, full_import_cache, incremental_import_cache, SPCONFIG_JSON

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = logging.Formatter('%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

backend = Backend()

def check_feature_supported(feature_list: List[str]) -> bool:
    for feature in feature_list:
        if feature in SUPPORTED_PROVISIONING_FEATURES:
            return True
    else:
        return False

class UsersSCIM(Resource):
    GET_FEATURES = [
        'PUSH_NEW_USERS',
        'PUSH_PENDING_USERS',
        'IMPORT_NEW_USERS',
        'OPP_SCIM_INCREMENTAL_IMPORTS'
    ]
    POST_FEATURES = [
        'PUSH_NEW_USER',
        'PUSH_PENDING_USERS'
    ]
    # retrieve users: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-users
    def get(self) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.GET_FEATURES): return make_response('', 501)
            # get url parameters
            args = request.args

            if 'filter' in args:
                filter_string = args['filter']
                logger.debug('Filter string received: %s' % filter_string)
                try:
                    FilterImplementation(filter_string)
                except FilterValidationError as e:
                    return handle_validation_error(e)
                if 'meta.lastModified' in filter_string:
                    import_type = 'incremental'
                else:
                    import_type = 'other'
            else:
                filter_string = None
                import_type = 'full'

            if 'startIndex' in args: 
                startIndex = int(args.get('startIndex'))
            else:
                startIndex = 1

            first_page: bool = startIndex == 1
            # if not doing an import (ex: getting user before create/update) dont bother
            # with the cache
            if import_type == 'other':
                logger.info('Non-import, calling DB')
                users = backend.list_users(filter=filter_string)
            # check if first page and no existing cache lock, if so, call DB
            elif first_page and ((import_type == 'full' and not full_import_cache.check_for_lock_file()) or (import_type == 'incremental' and not incremental_import_cache.check_for_lock_file())):
                logger.info('First page and no cache lock, reading users from database')
                users = backend.list_users(filter=filter_string)
            # else just get the users from the cache
            else:
                logger.info('Not the first page or the cache is locked, reading users from cache')
                # if its the first page but a lock file exists, append to it so it doesnt get removed
                # by another pagination process
                if first_page and ((import_type == 'full' and full_import_cache.check_for_lock_file()) or (import_type == 'incremental' and incremental_import_cache.check_for_lock_file())):
                    if import_type == 'full': full_import_cache.append_lock_file('start')
                    elif import_type == 'incremental': incremental_import_cache.append_lock_file('start')
                try:
                    if import_type == 'full':  users = full_import_cache.read_json_cache()
                    elif import_type == 'incremental': users = incremental_import_cache.read_json_cache()
                except (TimeoutError, FileNotFoundError):
                    logger.info('Error reading cache, either no longer valid or does not exist. Pulling from DB and saving new cache')
                    users = backend.list_users(filter=filter_string)
                    if import_type == 'full': full_import_cache.write_json_cache(obj_list_to_scim_json_list(users))
                    elif import_type == 'incremental': incremental_import_cache.write_json_cache(obj_list_to_scim_json_list(users))

            if 'totalResults' in args: 
                totalResults = int(args.get('totalResults'))
            else:
                totalResults = len(users)

            count = SPCONFIG_JSON['filter']['maxResults']
            if 'count' in args: 
                if int(args.get('count')) <= count:
                    count = int(args.get('count'))
            # if the total results are smaller than a page size
            if totalResults < count:
                count = totalResults
            # if on the last page and there was no count arg so default was used,
            # and default is larger than the remaining records, use the number of 
            # remaining records
            elif startIndex + count > totalResults + 1:
                count = totalResults - startIndex + 1

            # if first page, and there will be more than one page, and there is no current cache/lock,
            # write data to cache and create a cache lock
            if first_page and startIndex + count < totalResults + 1 and ((import_type == 'full' and not full_import_cache.check_for_lock_file()) or (import_type == 'incremental' and not incremental_import_cache.check_for_lock_file())):
                logger.info('First page of pagination and no cache lock, writing data to cache and creating lock')
                if import_type == 'full':
                    full_import_cache.write_json_cache(obj_list_to_scim_json_list(users))
                    full_import_cache.create_lock_file()
                elif import_type == 'incremental':
                    incremental_import_cache.write_json_cache(obj_list_to_scim_json_list(users))
                    incremental_import_cache.create_lock_file()
            # if last page clean up cache lock
            if startIndex + count == totalResults + 1 and not first_page:
                logger.info('Last page, attempting to clean up cache lock')
                if import_type == 'full':
                    full_import_cache.append_lock_file('end')
                    full_import_cache.cleanup_lock_file()
                elif import_type == 'incremental':
                    incremental_import_cache.append_lock_file('end')
                    incremental_import_cache.cleanup_lock_file()

            response: Response = jsonify(ListResponse(users[startIndex-1:startIndex-1+count], startIndex, count, totalResults).scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 200
            return response
        except Exception as e:
            return handle_server_side_error(e)

    # create user: https://developer.okta.com/docs/reference/scim/scim-20/#create-the-user
    def post(self) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.POST_FEATURES): return make_response('', 501)
        except Exception as e:
            return handle_server_side_error(e)
        
        # get request JSON, error out if invalid
        try:
            scim_json = request.get_json(force=True)
        except Exception as e:
            return handle_validation_error(e)

        try:
            in_scim_user = SCIMUser(scim_json, init_type='scim')
            logger.debug('Input: %s' % in_scim_user.scim_resource)
            out_scim_user = backend.create_user(in_scim_user)
            response: Response = jsonify(out_scim_user.scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 201
            return response
        except Exception as e:
            return handle_server_side_error(e)


class UserSpecificSCIM(Resource):
    GET_FEATURES = [
        'IMPORT_PROFILE_UPDATES'
    ]
    PUT_FEATURES = [
        'PUSH_PASSWORD_UPDATES',
        'PUSH_PENDING_USERS',
        'PUSH_PROFILE_UPDATES',
        'PUSH_USER_DEACTIVATION',
        'REACTIVATE_USERS'
    ]
    # get a specific user: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-a-specific-user
    def get(self, user_id: str) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.GET_FEATURES): return make_response('', 501)

            scim_user: SCIMUser = backend.get_user(user_id)
            if scim_user is not None:
                list_resp = ListResponse([scim_user], start_index=1, count=None, total_results=1)
            else:
                list_resp = ListResponse([])
            response: Response = jsonify(list_resp.scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 200
            return response
        except Exception as e:
            return handle_server_side_error(e)

    # update a specific user: https://developer.okta.com/docs/reference/scim/scim-20/#update-a-specific-user-put
    # this is also used for user deactivations in AIN apps
    def put(self, user_id: str) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.PUT_FEATURES): return make_response('', 501)
        except Exception as e:
            return handle_server_side_error(e)

        # get request JSON, error out if invalid
        try:
            scim_json = request.get_json(force=True)
        except Exception as e:
            return handle_validation_error(e)

        try:
            in_scim_user = SCIMUser(scim_json, init_type='scim')
            logger.debug('Input: %s' % in_scim_user.scim_resource)
            out_scim_user = backend.update_user(in_scim_user)
            response: Response = jsonify(out_scim_user.scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 200
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