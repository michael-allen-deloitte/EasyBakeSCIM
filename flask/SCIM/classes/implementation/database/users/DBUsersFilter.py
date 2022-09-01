from typing import Tuple
from datetime import datetime

from SCIM import USERNAME_FIELD
from SCIM.classes.generic.Filter import Filter, FilterValidationError
from SCIM.classes.implementation.database.models import UsersDB

class DBUsersFilter(Filter):
    def set_search_key_and_value(self, filter_args: Tuple[str]):
        # this always needs to be mapped, in this case the
        # userName coming from Okta is mapped to the "email"
        # column in the database. This can also be seen in 
        # models.py.
        if filter_args == USERNAME_FIELD:
            # MAPPING IMPLEMENTATION HERE, SET PROPER DATA TYPE
            self.search_value = filter_args[2]
            try:
                # MAPPING IMPLEMENTATION HERE, CONFIGURE USERNAME_FILED
                # DB OBJECT PROPERTY MAPPING IN CASE PROPERTY NAME
                # IS DIFFERENT FROM INCOMING KEY
                self.search_key = getattr(UsersDB, 'email')
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        # id always needs to be mapped to the column that would be the
        # "externalId" in the okta app profile
        elif filter_args[0] == 'id':
            # MAPPING IMPLEMENTATION HERE, SET PROPER DATA TYPE
            self.search_value = filter_args[2]
            try:
                # MAPPING IMPLEMENTATION HERE, CONFIGURE 'id'
                # DB OBJECT PROPERTY MAPPING IN CASE PROPERTY NAME
                # IS DIFFERENT FROM INCOMING KEY
                self.search_key = getattr(UsersDB, filter_args[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        # this needs to be mapped if incremental imports are allowed
        elif filter_args[0] == 'meta.lastModified':
            try:
                # MAPPING IMPLEMENTATION HERE, SET PROPER DATA TYPE
                self.search_value = datetime.fromisoformat(filter_args[2].strip('Z'))
                # if database has lastModified as date and not datetime
                # self.search_value = datetime.date(self.search_value)
            except ValueError as e:
                raise FilterValidationError(message=str(e))
            try:
                # MAPPING IMPLEMENTATION HERE, CONFIGURE lastModified
                # DB OBJECT PROPERTY MAPPING IN CASE PROPERTY NAME
                # IS DIFFERENT FROM INCOMING KEY
                self.search_key = getattr(UsersDB, 'lastModified')
            except AttributeError as e:
                raise FilterValidationError(message=str(e))

        # MAPPING IMPLEMENTATION HERE (most likely will not need, but here for example)
        # ADD CASE FOR EACH ATTRIBUTE THAT CAN BE FILTERED ON
        # these extensions are used as an example of filtering on other attributes
        # (and other attribute types), unsure if Okta even does this but the example
        # on how to implement in case of need is below
        elif filter_args[0] == 'number':
            # MAPPING IMPLEMENTATION HERE, SET PROPER DATA TYPE
            self.search_value = int(filter_args[2])
            try:
                # MAPPING IMPLEMENTATION HERE, CONFIGURE number
                # DB OBJECT PROPERTY MAPPING IN CASE PROPERTY NAME
                # IS DIFFERENT FROM INCOMING KEY
                self.search_key = getattr(UsersDB, filter_args[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        elif filter_args[0] == 'active':
            try:
                # MAPPING IMPLEMENTATION HERE, CONFIGURE active
                # DB OBJECT PROPERTY MAPPING IN CASE PROPERTY NAME
                # IS DIFFERENT FROM INCOMING KEY
                self.search_key = getattr(UsersDB, filter_args[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
            # MAPPING IMPLEMENTATION HERE, SET PROPER DATA TYPE
            self.search_value = filter_args[2].lower().strip() == 'true'

        # throw a validation error if a search key that is not mapped is received
        else:
            raise FilterValidationError(message='The search key \"%s\" has not been mapped in the Filter Implementation' % filter_args[0])