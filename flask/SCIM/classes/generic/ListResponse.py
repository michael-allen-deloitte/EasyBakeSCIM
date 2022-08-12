from typing import List, Union

from SCIM.classes.generic.SCIMUser import SCIMUser

class ListResponse:
    def __init__(self, list: Union[List[SCIMUser], List[dict]], start_index:int=1, count:int=None, total_results:int=0):
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
        if self.list != [] and type(self.list[0]) == SCIMUser:
            for item in self.list:
                resources.append(item.scim_resource)
        else:
            resources = self.list
        if self.count:
            rv['itemsPerPage'] = self.count
        rv['Resources'] = resources
        return rv