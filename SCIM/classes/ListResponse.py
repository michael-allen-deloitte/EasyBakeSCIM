class ListResponse():
    def __init__(self, list, start_index=1, count=None, total_results=0):
        self.list = list
        self.start_index = start_index
        self.count = count
        self.total_results = total_results

    def to_scim_resource(self):
        rv = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": self.total_results,
            "startIndex": self.start_index,
            "Resources": []
        }
        resources = []
        for item in self.list:
            resources.append(item.to_scim_resource())
        if self.count:
            rv['itemsPerPage'] = self.count
        rv['Resources'] = resources
        return rv