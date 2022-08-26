from datetime import datetime
from SCIM.classes.generic.Filter import Filter, FilterValidationError
from SCIM.classes.implementation.database.models import UsersDB
from typing import Tuple

class CustomFilter(Filter):
    def find_nonstandard_value_type(self, split_filter: Tuple[str]):
        if split_filter[0] == 'number':
            self.search_value = int(split_filter[2])
            try:
                self.search_key = getattr(UsersDB, split_filter[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        elif split_filter[0] =='active':
            try:
                self.search_key = getattr(UsersDB, split_filter[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
            self.search_value = split_filter[2].lower().strip() == 'true'
        elif split_filter[0] =='userName':
            self.search_value = split_filter[2]
            try:
                self.search_key = getattr(UsersDB, 'email')
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        # if database has lastModified as date and not datetime
        #elif split_filter[0] == 'meta.lastModified':
        #    self.search_value = datetime.date(self.search_value)