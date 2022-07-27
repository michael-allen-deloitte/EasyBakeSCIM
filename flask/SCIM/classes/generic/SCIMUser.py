from flask import url_for

from SCIM import APP_SCHEMA

# this class is used to convert scim objects to a python oject, and vice versa
# this class is meant to be general and work for all backends, therefore the backend conversion portions will be split from this
class SCIMUser:
    def __init__(self, resource, init_type='scim'):
        self.id = ""
        self.active: bool
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
        if init_type == 'scim':
            self.update_from_scim(resource)
        elif init_type == 'backend':
            self.update_from_backend(resource)
        self.appSchema = APP_SCHEMA

    # this function is used to convert the SCIM object to this User object
    # examples can be found here: https://developer.okta.com/docs/reference/scim/scim-20/
    def update_from_scim(self, resource: dict) -> None:
        keys = dict(resource).keys()
        customKey = ""
        for key in keys:
            if "urn:okta:" in key:
                customKey = key
            # example phone number obj: 'phoneNumbers': [{'value': '123-654-4815', 'primary': True, 'type': 'mobile'}]
            if 'phoneNumbers' in key:
                for number in resource[key]:
                    if number['primary']:
                        self.mobilePhone = number['value']
        for attribute in ['userName', 'active', 'password']:
            if attribute in resource:
                setattr(self, attribute, resource[attribute])
        for attribute in ['givenName', 'middleName', 'familyName']:
            if attribute in resource['name']:
                setattr(self, attribute, resource['name'][attribute])
        try:
            for attribute in resource['emails']:
                if attribute['primary']:
                    self.email = attribute['value']
                else:
                    self.secondaryEmail = attribute['value']
        except KeyError:
            pass
        # get custom attributes
        try:
            for attribute in resource[customKey]:
                self.custom_attributes[attribute] = resource[customKey][attribute]
        except KeyError:
            pass

    # this function is used by the backend to populate this object, it takes in a generic dict with all the attributes
    def update_from_backend(self, resource: dict) -> None:
        keys = dict(resource).keys()
        if 'id' in keys: self.id = resource['id']
        if 'active' in keys: self.active = resource['active']
        if 'userName' in keys: self.userName = resource['userName']
        if 'familyName' in keys: self.familyName = resource['familyName']
        if 'middleName' in keys: self.middleName = resource['middleName']
        if 'givenName' in keys: self.givenName = resource['givenName']
        if 'email' in keys: self.email = resource['email']
        if 'secondaryEmail' in keys: self.secondaryEmail = resource['secondaryEmail']
        if 'mobilePhone' in keys: self.mobilePhone = resource['mobilePhone']
        if 'password' in keys: self.password = resource['password']
        if 'custom_attributes' in keys: self.custom_attributes = resource['custom_attributes']
        


    # this function is used to convert this User object to a SCIM formatted dict to be returned to Okta
    @property
    def scim_resource(self) -> dict:
        if self.secondaryEmail == "":
            emails = [
                {
                    "primary": True,
                    "value": self.email,
                    "type": "primary"
                }
            ]
        else:
            emails = [
                {
                    "primary": True,
                    "value": self.email,
                    "type": "primary"
                },
                {
                    "primary": False,
                    "value": self.secondaryEmail,
                    "type": "secondary"
                }
            ]
        rv = {
            "schemas": ["urn:scim:schemas:extension:enterprise:1.0", "urn:okta:%s:1.0:user:custom" % self.appSchema, "urn:scim:schemas:core:1.0"],
            "id": self.id,
            "userName": self.userName,
            "name": {
                "familyName": self.familyName,
                "givenName": self.givenName,
                "middleName": self.middleName,
            },
            "active": self.active,
            "meta": {
                "resourceType": "User",
                "location": url_for('user_get',
                                    user_id=self.id,
                                    _external=True)
                # "created": "2010-01-23T04:56:22Z",
                # "lastModified": "2011-05-13T04:42:34Z",
            },
            "emails": emails,
            "urn:okta:%s:1.0:user:custom" % self.appSchema: self.custom_attributes
        }
        if self.mobilePhone != "":
            phone_numbers = [
                {
                    "primary": True,
                    "value": self.mobilePhone,
                    "type": "mobile"
                }
            ]
            rv['phoneNumbers'] = phone_numbers
        return rv