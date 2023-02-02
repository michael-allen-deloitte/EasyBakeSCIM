from typing import List, Union

from SCIM.classes.generic.SCIMGroup import SCIMGroup

# this is inteded to be used as an interface which is extended for a specific backend
class GroupsBackend:
    # return None if a group with group_id cannot be found
    def get_group(self, group_id: str) -> Union[SCIMGroup, None]:
        return None

    # return an empty list if no groups were found
    def list_groups(self, filter: str=None) -> List[SCIMGroup]:
        return []

    def create_group(self, scim_group: SCIMGroup) -> SCIMGroup:
        pass

    def update_group(self, scim_group: SCIMGroup) -> SCIMGroup:
        pass

    # return None on a successful delete
    def delete_group(self, group_id: str) -> None:
        return None