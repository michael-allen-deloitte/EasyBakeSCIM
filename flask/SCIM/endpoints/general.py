from traceback import format_exc
from flask import Response, jsonify, make_response
from flask_restful import Resource

from SCIM.helpers import scim_error, create_spconfig_json, set_up_logger
from SCIM.classes.generic.Cache import Cache

logger = set_up_logger(__name__)

full_import_cache = Cache('full_import_cache.json')
incremental_import_cache = Cache('incremental_import_cache.json')
full_import_groups_cache = Cache('full_import_groups_cache.json')
incremental_import_groups_cache = Cache('incremental_import_groups_cache.json')

SPCONFIG_JSON: dict = create_spconfig_json()

def handle_server_side_error(e: Exception) -> Response:
    error_json = scim_error("An unexpected error has occured: %s" % e, 500, format_exc())
    error_response = make_response(error_json, 500)
    logger.error(error_json)
    return error_response

def handle_validation_error(e: Exception) -> Response:
    error_json = scim_error("An validation error has occured: %s" % e, 400, format_exc())
    error_response = make_response(error_json, 400)
    logger.error(error_json)
    return error_response

class ServiceProviderConfigSCIM(Resource):
    def get(self) -> Response:
        try:
            response: Response = jsonify(SPCONFIG_JSON)
            logger.debug('Response: %s' % response.get_json())
            response.status_code = 200
            return response
        except Exception as e:
            return handle_server_side_error(e)

class ClearCache(Resource):
    def get(self) -> Response:
        try:
            full_import_cache.force_clear_cache()
            incremental_import_cache.force_clear_cache()
            return make_response('', 204)
        except Exception as e:
            return handle_server_side_error(e)

class HealthCheck(Resource):
    def get(self) -> Response:
        return make_response('', 200)