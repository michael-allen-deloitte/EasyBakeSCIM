from typing import List, Union

from SCIM.classes.generic.SCIMUser import SCIMUser

# this is inteded to be used as an interface which is extended for a specific backend
class UserBackend:
    # returns None if a user with user_id cannot be found
    def get_user(self, user_id: str) -> Union[SCIMUser, None]:
        return None

    # returns an empty list if there were no users found 
    def list_users(self, filter: str=None) -> List[SCIMUser]:
        return []

    def create_user(self, scim_user: SCIMUser) -> SCIMUser:
        pass

    def update_user(self, scim_user: SCIMUser) -> SCIMUser:
        pass

    # should only be called in PATCH
    # not supported in OPP conectors yet
    def enable_user(self, scim_user: SCIMUser) -> SCIMUser:
        pass

    # should only be called in PATCH
    # not supported in OPP conectors yet
    def disable_user(self, scim_user: SCIMUser) -> SCIMUser:
        pass

    # this should only be used if the password can't be updated with the user profile at the same time (if the password is stored somewhere else)
    def reset_password(self, scim_user: SCIMUser) -> SCIMUser:
        pass