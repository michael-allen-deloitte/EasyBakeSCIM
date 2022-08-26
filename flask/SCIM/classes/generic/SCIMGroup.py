from typing import List

# this class is used to convert scim objects to a python oject, and vice versa
# this class is meant to be general and work for all backends, therefore the backend conversion portions will be split from this
class SCIMGroup(object):
    def __init__(self, resource, init_type='scim'):
        self.id = ""
        self.displayName = ""
        self.members: List[dict] = []
        # there are no custom attributes in this lab but we will leave this here as it does not impact anything else
        # and keeping it will make it easier to extend with a custom attribute in the future
        self.custom_attributes = {}
        if init_type == 'scim':
            self.update_from_scim(resource)
        elif init_type == 'backend':
            self.update_from_backend(resource)

    # this function is used to convert the SCIM object to this Groups object
    # examples can be found here: https://developer.okta.com/docs/reference/scim/scim-20/
    def update_from_scim(self, resource: dict) -> None:
        for attribute in ['displayName', 'members', 'id']:
            if attribute in resource:
                setattr(self, attribute, resource[attribute])
        # get custom attributes
        try:
            for attribute in resource['urn:okta:custom:group:1.0']:
                self.custom_attributes[attribute] = resource['urn:okta:custom:group:1.0'][attribute]
        except KeyError:
            pass

    # this function is used by the backend to populate this object, it takes in a generic dict with all the attributes
    def update_from_backend(self, resource: dict) -> None:
        keys = dict(resource).keys()
        if 'id' in keys: self.id = resource['id']
        if 'displayName' in keys: self.active = resource['displayName']
        if 'members' in keys: self.userName = resource['members']
        if 'custom_attributes' in keys: self.custom_attributes = resource['custom_attributes']
        


    # this function is used to convert this Group object to a SCIM formatted dict to be returned to Okta
    @property
    def scim_resource(self) -> dict:
        rv = {
            "schemas": ["urn:okta:custom:group:1.0" "urn:scim:schemas:core:1.0"],
            "id": self.id,
            "displayName": self.displayName,
            "members": self.members,
            #"meta": {
            #    "resourceType": "User",
            #    "location": url_for('user_get',
            #                        user_id=self.id,
            #                        _external=True)
                # "created": "2010-01-23T04:56:22Z",
                # "lastModified": "2011-05-13T04:42:34Z",
            #},
            "urn:okta:custom:group:1.0": self.custom_attributes
        }
        return rv

def obj_list_to_scim_json_list(scim_user_obj_list: List[SCIMGroup]) -> List[dict]:
    out = []
    for obj in scim_user_obj_list:
        out.append(obj.scim_resource)
    return out