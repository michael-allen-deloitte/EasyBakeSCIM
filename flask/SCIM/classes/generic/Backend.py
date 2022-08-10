from typing import List

from SCIM.classes.generic.SCIMUser import SCIMUser

# this is inteded to be used as an interface which is extended for a specific backend
class UserBackend:
    def get_user(self, user_id: str) -> SCIMUser:
        # code to get user object here
        # this function must take a username and return None or a User object
        return None

    def list_users(self, filter=None) -> List[SCIMUser]:
        # code to get all users here
        # this function should take a filter (possibly, may implement later) and return a list of User objects
        return []

    def create_user(self, scim_user: SCIMUser) -> SCIMUser:
        # code to create a user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    def update_user(self, scim_user: SCIMUser) -> SCIMUser:
        # code to update user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    # should only be called in PATCH
    def enable_user(self, scim_user: SCIMUser) -> SCIMUser:
        # code to enable user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    # should only be called in PATCH
    def disable_user(self, scim_user: SCIMUser) -> SCIMUser:
        # code to disable user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    # this should only be used if the password can't be updated with the user profile at the same time (if the password is stored somewhere else)
    def reset_password(self, scim_user: SCIMUser) -> SCIMUser:
        # code to reset the users password
        # this function should take a User object and return nothing, only error out if there was an issue
        # the user object should contain the password in user.password
        pass