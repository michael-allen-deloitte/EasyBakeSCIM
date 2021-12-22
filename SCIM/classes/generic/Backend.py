from typing import List

from SCIM.classes.generic.SCIMUser import SCIMUser

# this is inteded to be used as an interface which is extended for a specific backend
class UserBackend:
    """
    # this is a placeholder until implementation design can be determined
    def __init__(self, resource, source='scim') -> None:
        self.id = ""
        self.active = ""
        self.userName = ""
        self.familyName = ""
        self.middleName = ""
        self.givenName = ""
        self.email = ""
        self.secondaryEmail = ""
        # for this object we are assuming only one phone number and that it is always has type 'mobile'
        self.mobilePhone = ""
        self.password = ""
        # there are no custom attributes in this lab but we will leave this here as it does not impact anything else
        # and keeping it will make it easier to extend with a custom attribute in the future
        self.custom_attributes = {}
        if source == 'scim':
            self.update_from_scim(resource)
        elif source == 'backend':
            self.update_from_backend(resource)
        if self.id == "":
            self.id = self.userName

    def update_from_scim(self, user: SCIMUser) -> None:
        self.id = user.id
        self.active = user.active
        self.userName = user.userName
        self.familyName = user.familyName
        self.middleName = user.middleName
        self.givenName = user.givenName
        self.email = user.email
        self.secondaryEmail = user.secondaryEmail
        self.mobilePhone = user.mobilePhone
        self.password = user.password
        self.custom_attributes = user.custom_attributes

    def update_from_backend(self, resource) -> None:
        
        return None

    """
        
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

    def reset_password(self, scim_user: SCIMUser) -> SCIMUser:
        # code to reset the users password
        # this function should take a User object and return nothing, only error out if there was an issue
        # the user object should contain the password in user.password
        pass