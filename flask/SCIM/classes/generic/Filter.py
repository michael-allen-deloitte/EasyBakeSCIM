from re import match
import datetime
from typing import Tuple
from SCIM.classes.implementation.database.models import UsersDB

class Filter:
    def __init__(self, filter: str) -> None:
        if '"' in filter:
            filter_match = match('(\w+) (\w+) "([^"]*)"', filter)
        else:
            filter_match = match('(\w+) (\w+) ([a-zA-Z0-9_]+)', filter)

        filter_args = filter_match.groups()

        self.search_key = getattr(UsersDB, filter_args[0])
        self.comparator = filter_args[1]

        if filter_args[0] == 'id':
            self.search_value = str(filter_args[2])
        elif filter_args[0] == 'meta.lastModified':
            self.search_value = datetime.datetime.fromisoformat(filter_args[2])
        else:
            self.find_nonstandard_value_type(filter_args)

    def find_nonstandard_value_type(self, split_filter: Tuple[str]):
        pass