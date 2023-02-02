from flask import Flask
from flask_restful import Api
from typing import List

from SCIM.helpers import config

BACKEND_TYPE: str = config['General']['backend_type'].lower()
# init this to False, read from config if the backend is a DB
LOCAL_DATABASE = False
APP_SCHEMA: str = config['Okta']['schema']
USERNAME_FIELD: str = config['Okta']['username_field']

app: Flask = Flask(__name__)
app.logger.handlers.clear()
api: Api = Api(app)

if BACKEND_TYPE == 'database':
    from flask_sqlalchemy import SQLAlchemy
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    LOCAL_DATABASE = config['Database']['local'].lower() == 'true'
    if LOCAL_DATABASE:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
    else:
        # https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls
        app.config['SQLALCHEMY_DATABASE_URI'] = '%s://%s:%s@%s/%s' % (config['Database']['dialect_driver_string'], config['Database']['username'], config['Database']['password'], config['Database']['host'], config['Database']['database'])
    db = SQLAlchemy(app)

possible_provisioning_features = config['SCIM Features'].keys()
SUPPORTED_PROVISIONING_FEATURES: List[str] = []
for feature in possible_provisioning_features:
    if config['SCIM Features'][feature].lower() == 'true': SUPPORTED_PROVISIONING_FEATURES.append(feature.upper())

users_features = [
    'PUSH_NEW_USERS',
    'PUSH_PENDING_USERS',
    'IMPORT_NEW_USERS',
    'OPP_SCIM_INCREMENTAL_IMPORTS'
]
user_specific_features = [
    'PUSH_PASSWORD_UPDATES',
    'PUSH_PENDING_USERS',
    'PUSH_PROFILE_UPDATES',
    'PUSH_USER_DEACTIVATION',
    'REACTIVATE_USERS',
    'IMPORT_PROFILE_UPDATES'
]
groups_features = [
    'GROUP_PUSH',
    'IMPORT_GROUPS_WITH_USERS'
]
group_specific_features = ['GROUP_PUSH']

from SCIM.endpoints.general import ServiceProviderConfigSCIM, ClearCache, HealthCheck
api.add_resource(ServiceProviderConfigSCIM, '/ServiceProviderConfigs')
api.add_resource(ClearCache, '/ClearCache')
api.add_resource(HealthCheck, '/')

for feature in users_features:
    if feature in SUPPORTED_PROVISIONING_FEATURES:
        from SCIM.endpoints.users import UsersSCIM
        api.add_resource(UsersSCIM, '/Users')
        break
for feature in user_specific_features:
    if feature in SUPPORTED_PROVISIONING_FEATURES:
        from SCIM.endpoints.users import UserSpecificSCIM
        api.add_resource(UserSpecificSCIM, '/Users/<user_id>')
        break
for feature in groups_features:
    if feature in SUPPORTED_PROVISIONING_FEATURES:
        from SCIM.endpoints.groups import GroupsSCIM
        api.add_resource(GroupsSCIM, '/Groups')
        break
for feature in group_specific_features:
    if feature in SUPPORTED_PROVISIONING_FEATURES:
        from SCIM.endpoints.groups import GroupsSpecificSCIM
        api.add_resource(GroupsSpecificSCIM, '/Groups/<group_id>')
        break