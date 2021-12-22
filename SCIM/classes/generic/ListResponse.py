from typing import List

from SCIM.classes.generic.SCIMUser import SCIMUser

class ListResponse():
    def __init__(self, list: List[SCIMUser], start_index:int=1, count:int=None, total_results:int=0):
        self.list = list
        self.start_index = start_index
        self.count = count
        self.total_results = total_results

    @property
    def scim_resource(self) -> dict:
        rv = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": self.total_results,
            "startIndex": self.start_index,
            "Resources": []
        }
        resources = []
        for item in self.list:
            resources.append(item.scim_resource)
        if self.count:
            rv['itemsPerPage'] = self.count
        rv['Resources'] = resources
        return rv