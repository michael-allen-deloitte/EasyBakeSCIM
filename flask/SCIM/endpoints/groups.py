from typing import List
from flask import request, jsonify, make_response, Response
from flask_restful import Resource

from SCIM import SUPPORTED_PROVISIONING_FEATURES
from SCIM.helpers import set_up_logger
from SCIM.endpoints.general import handle_server_side_error, handle_validation_error, full_import_groups_cache, incremental_import_groups_cache, SPCONFIG_JSON
from SCIM.classes.generic.SCIMGroup import SCIMGroup, obj_list_to_scim_json_list
from SCIM.classes.generic.ListResponse import ListResponse
# import our specific class as a generic Backend name, so that only the class being imported needs to be modified and the rest of the code runs the same
# all specific implementations should be subclasses of the SCIM.classes.generic.Backend.UserBackend class
#from SCIM.classes.implementation.database.DBBackend import DBBackend as Backend
from SCIM.classes.implementation.database.groups.DBGroupsBackend import DBGroupsBackend as Backend

logger = set_up_logger(__name__)

backend = Backend()

def check_feature_supported(feature_list: List[str]) -> bool:
    for feature in feature_list:
        if feature in SUPPORTED_PROVISIONING_FEATURES:
            return True
    else:
        return False

class GroupsSCIM(Resource):
    GET_FEATURES = [
        'IMPORT_GROUPS_WITH_USERS'
    ]
    POST_FEATURES = [
        'GROUP_PUSH'
    ]
    # retreive groups: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-groups
    def get(self) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.GET_FEATURES): return make_response('', 501)
            
            # get url parameters
            args = request.args

            if 'startIndex' in args: 
                startIndex = int(args.get('startIndex'))
            else:
                startIndex = 1

            if 'filter' in args:
                filter_string = args['filter']
                logger.debug('Filter string received: %s' % filter_string)
                if 'meta.lastModified' in filter_string:
                    import_type = 'incremental'
                else:
                    import_type = 'other'
            else:
                filter_string = None
                import_type = 'full'

            first_page: bool = startIndex == 1
            # if not doing an import (ex: getting user before create/update) dont bother
            # with the cache
            if import_type == 'other':
                logger.info('Non-import, calling backend')
                groups = backend.list_groups(filter=filter_string)
            # check if first page and no existing cache lock, if so, call DB
            elif first_page and ((import_type == 'full' and not full_import_groups_cache.check_for_lock_file()) or (import_type == 'incremental' and not incremental_import_groups_cache.check_for_lock_file())):
                logger.info('First page and no cache lock, reading groups from backend')
                groups = backend.list_groups(filter=filter_string)
            # else just get the users from the cache
            else:
                logger.info('Not the first page or the cache is locked, reading groups from cache')
                # if its the first page but a lock file exists, append to it so it doesnt get removed
                # by another pagination process
                if first_page and ((import_type == 'full' and full_import_groups_cache.check_for_lock_file()) or (import_type == 'incremental' and incremental_import_groups_cache.check_for_lock_file())):
                    if import_type == 'full': full_import_groups_cache.append_lock_file('start')
                    elif import_type == 'incremental': incremental_import_groups_cache.append_lock_file('start')
                try:
                    if import_type == 'full':  groups = full_import_groups_cache.read_json_cache()
                    elif import_type == 'incremental': groups = incremental_import_groups_cache.read_json_cache()
                except (TimeoutError, FileNotFoundError):
                    logger.info('Error reading cache, either no longer valid or does not exist. Pulling from backend and saving new cache')
                    groups = backend.list_groups(filter=filter_string)
                    if import_type == 'full': full_import_groups_cache.write_json_cache(obj_list_to_scim_json_list(groups))
                    elif import_type == 'incremental': incremental_import_groups_cache.write_json_cache(obj_list_to_scim_json_list(groups))

            if 'totalResults' in args: 
                totalResults = int(args.get('totalResults'))
            else:
                totalResults = len(groups)

            if 'count' in args: 
                count = int(args.get('count'))
            else:
                count = SPCONFIG_JSON['filter']['maxResults']
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
            if first_page and startIndex + count < totalResults + 1 and ((import_type == 'full' and not full_import_groups_cache.check_for_lock_file()) or (import_type == 'incremental' and not incremental_import_groups_cache.check_for_lock_file())):
                logger.info('First page of pagination and no cache lock, writing data to cache and creating lock')
                if import_type == 'full':
                    full_import_groups_cache.write_json_cache(obj_list_to_scim_json_list(groups))
                    full_import_groups_cache.create_lock_file()
                elif import_type == 'incremental':
                    incremental_import_groups_cache.write_json_cache(obj_list_to_scim_json_list(groups))
                    incremental_import_groups_cache.create_lock_file()
            # if last page clean up cache lock
            if startIndex + count == totalResults + 1 and not first_page:
                logger.info('Last page, attempting to clean up cache lock')
                if import_type == 'full':
                    full_import_groups_cache.append_lock_file('end')
                    full_import_groups_cache.cleanup_lock_file()
                elif import_type == 'incremental':
                    incremental_import_groups_cache.append_lock_file('end')
                    incremental_import_groups_cache.cleanup_lock_file()

            response: Response = jsonify(ListResponse(groups[startIndex-1:startIndex-1+count], startIndex, count, totalResults).scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 200
            return response

        except Exception as e:
            return handle_server_side_error(e)

    # create group: https://developer.okta.com/docs/reference/scim/scim-20/#create-groups
    def post(self) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.POST_FEATURES): make_response('', 501)
            pass
        except Exception as e:
            return handle_server_side_error(e)

        # get request JSON, error out if invalid
        try:
            scim_json = request.get_json(force=True)
        except Exception as e:
            return handle_validation_error(e)

        try:
            in_scim_group = SCIMGroup(scim_json, init_type='scim')
            logger.debug('Input: %s' % in_scim_group.scim_resource)
            out_scim_group = backend.create_group(in_scim_group)
            response: Response = jsonify(out_scim_group.scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 201
            return response
        except Exception as e:
            return handle_server_side_error(e)


class GroupsSpecificSCIM(Resource):
    GET_FEATURES = [
        'GROUP_PUSH'
    ]
    PUT_FEATURES = [
        'GROUP_PUSH'
    ]
    DELETE_FEATURES = [
        'GROUP_PUSH'
    ]
    # retreive specific group: https://developer.okta.com/docs/reference/scim/scim-20/#retrieve-specific-groups
    def get(self, group_id: str) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.GET_FEATURES): return make_response('', 501)
            
            scim_group: SCIMGroup = backend.get_group(group_id)
            if scim_group is not None:
                list_resp = ListResponse([scim_group], start_index=1, count=None, total_results=1)
            else:
                list_resp = ListResponse([])
            response: Response = jsonify(list_resp.scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 200
            return response
        except Exception as e:
            return handle_server_side_error(e)

    # update group name: https://developer.okta.com/docs/reference/scim/scim-20/#update-a-specific-group-name
    # update group membership: https://developer.okta.com/docs/reference/scim/scim-20/#update-specific-group-membership
    def put(self, group_id: str) -> Response:
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
            in_scim_group = SCIMGroup(scim_json, init_type='scim')
            logger.debug('Input: %s' % in_scim_group.scim_resource)
            out_scim_group = backend.update_group(in_scim_group)
            response: Response = jsonify(out_scim_group.scim_resource)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 200
            return response
        except Exception as e:
            return handle_server_side_error(e)

    # update group name: https://developer.okta.com/docs/reference/scim/scim-20/#update-a-specific-group-name
    # update group membership: https://developer.okta.com/docs/reference/scim/scim-20/#update-specific-group-membership
    # this is for OIN applications, not currently supported for OPP
    """
    def patch(self, group_id: str):
        try:
            pass
        except Exception as e:
            return handle_server_side_error(e)
    """

    # delete group: https://developer.okta.com/docs/reference/scim/scim-20/#delete-a-specific-group
    def delete(self, group_id: str) -> Response:
        try:
            # if this method is not needed for the supported features return a 501 Not Implemented
            if not check_feature_supported(self.DELETE_FEATURES): return make_response('', 501)
            backend.delete_group(group_id)
            return make_response('', 204)
        except Exception as e:
            return handle_server_side_error(e)