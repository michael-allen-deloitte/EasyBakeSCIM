from SCIM.classes import User

class Backend:
    # this is a placeholder until implementation design can be determined
    def __init__(self, backend_type='mysql'):
        self.backend_type = backend_type

    def get_user(self, user_id):
        # code to get user object here
        # this function must take a username and return None or a User object
        return None

    def get_all_users(self, filter=None):
        # code to get all users here
        # this function should take a filter (possibly, may implement later) and return a list of User objects
        return []

    def create_user(self, user):
        # code to create a user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    def update_user(self, user):
        # code to update user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    def enable_user(self, user):
        # code to enable user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    def disable_user(self, user):
        # code to disable user here
        # this function should take a User object and return nothing, only error out if there was an issue
        pass

    def reset_password(self, user):
        # code to reset the users password
        # this function should take a User object and return nothing, only error out if there was an issue
        # the user object should contain the password in user.password
        pass