from datetime import datetime
from SCIM.classes.generic.Filter import Filter
from typing import Tuple

class CustomFilter(Filter):
    def find_nonstandard_value_type(self, split_filter: Tuple[str]):
        if split_filter[0] == 'number':
            self.search_value = int(split_filter[2])
        elif split_filter[0] =='active':
            if split_filter[2] == 'true':
                self.search_value = True
            else:
                self.search_value = False
        # if database has lastModified as date and not datetime
        elif split_filter[0] == 'meta.lastModified':
            self.search_value = datetime.date(self.search_value)