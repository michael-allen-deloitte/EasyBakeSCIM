from re import match
from datetime import datetime
from typing import Tuple
from SCIM.classes.implementation.database.models import UsersDB

class FilterValidationError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Filter:
    def __init__(self, filter: str) -> None:
        if '"' in filter:
            match_string = '([\w\._-]+) (\w+) "([^"]*)"'
            filter_match = match(match_string, filter)
        else:
            match_string = '([\w\._-]+) (\w+) ([a-zA-Z0-9_]+)'
            filter_match = match(match_string, filter)

        try:
            filter_args = filter_match.groups()
        except AttributeError:
            raise FilterValidationError(message='Error in REGEX expression matching (%s) of filter string, unable to parse filter string: %s' % (match_string, filter))
        self.comparator = filter_args[1]
        if self.comparator not in ['lt', 'gt', 'eq']:
            raise FilterValidationError(message='Comparator must be one of [lt, gt, eq], value received was: %s' % self.comparator)

        if filter_args[0] == 'id':
            self.search_value = filter_args[2]
            try:
                self.search_key = getattr(UsersDB, filter_args[0])
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        elif filter_args[0] == 'meta.lastModified':
            try:
                self.search_value = datetime.fromisoformat(filter_args[2].strip('Z'))
            except ValueError as e:
                raise FilterValidationError(message=str(e))
            try:
                self.search_key = getattr(UsersDB, 'lastModified')
            except AttributeError as e:
                raise FilterValidationError(message=str(e))
        else:
            self.find_nonstandard_value_type(filter_args)

    def find_nonstandard_value_type(self, split_filter: Tuple[str]):
        pass