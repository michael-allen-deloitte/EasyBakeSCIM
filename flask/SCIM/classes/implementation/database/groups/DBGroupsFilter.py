from datetime import datetime
from SCIM.classes.generic.Filter import Filter, FilterValidationError
from SCIM.classes.implementation.database.models import GroupsDB
from typing import Tuple

class DBGroupsFilter(Filter):
    def set_search_key_and_value(self, filter_args: Tuple[str]):
        # id always needs to be mapped
        if filter_args[0] == 'id':
            self.search_value = filter_args[2]
            try:
                self.search_key = getattr(GroupsDB, filter_args[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        # this needs to be mapped if incremental imports are allowed
        elif filter_args[0] == 'meta.lastModified':
            try:
                self.search_value = datetime.fromisoformat(filter_args[2].strip('Z'))
                # if database has lastModified as date and not datetime
                # self.search_value = datetime.date(self.search_value)
            except ValueError as e:
                raise FilterValidationError(message=str(e))
            try:
                self.search_key = getattr(GroupsDB, 'lastModified')
            except AttributeError as e:
                raise FilterValidationError(message=str(e))

        # these extensions are used as an example of filtering on other attributes
        # (and other attribute types), unsure if Okta even does this but the example
        # on how to implement in case of need is below
        elif filter_args[0] == 'displayName':
            self.search_value = filter_args[2]
            try:
                self.search_key = getattr(GroupsDB, filter_args[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        elif filter_args[0] =='description':
            self.search_value = filter_args[2]
            try:
                self.search_key = getattr(GroupsDB, filter_args[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))

        # throw a validation error if a search key that is not mapped is received
        else:
            raise FilterValidationError(message='The search key \"%s\" has not been mapped in the Filter Implementation' % filter_args[0])