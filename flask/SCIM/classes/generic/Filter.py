from re import match
from typing import Tuple

class FilterValidationError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Filter:
    def __init__(self, filter: str, ) -> None:
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

        self.set_search_key_and_value(filter_args)

    # filter_args takes the form (str(search_key), comparator, str(search_value))
    # the purpose of this function is to get the proper lookup key for search_key
    # and the proper datatype for search_value. For example, in a DB w/SQLalchemy we 
    # would need the DB Column attribute to search on, and data type of the value
    # needs to match the data type of the Column (can't do DB.query.filter(id='100'))
    # if the id column is an int and '100' is a string)
    def set_search_key_and_value(self, filter_args: Tuple[str]):
        pass