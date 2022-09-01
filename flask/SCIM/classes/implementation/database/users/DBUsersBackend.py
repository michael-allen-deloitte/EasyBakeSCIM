import logging
from uuid import uuid4
from typing import List
from datetime import datetime

from SCIM import db
from SCIM.helpers import set_up_logger, LOG_LEVEL
from SCIM.classes.generic.SCIMUser import SCIMUser
from SCIM.classes.generic.UsersBackend import UserBackend
from SCIM.classes.implementation.database.models import UsersDB, UsersGroupsAssociation
from SCIM.classes.implementation.database.users.DBUsersFilter import DBUsersFilter

logger = set_up_logger(__name__)

class DBUsersBackend(UserBackend):
    def get_user(self, user_id: str) -> SCIMUser:
        # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
        # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
        # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
        # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
        # name= input on the Column() constructor
        user_db_object: List[UsersDB] = UsersDB.query.filter_by(id=user_id).all()


        if len(user_db_object) > 1:
            logger.error('More than 1 object was found with the id:%s' % user_id)
            raise(LookupError, 'More than 1 object was found with the id:%s' % user_id)
        elif len(user_db_object) == 0:
            return None
        else:
            return user_db_object[0].scim_user

    def list_users(self, filter: str = None) -> List[SCIMUser]:
        out: List[SCIMUser] = []
        user_db_objs: List[UsersDB] = []

        # Check for filter, create one if needed, and query the users
        if filter is None:
            user_db_objs: List[UsersDB] = UsersDB.query.all()
        else:
            filter_obj = DBUsersFilter(filter)
            if filter_obj.comparator == 'lt':
                user_db_objs = UsersDB.query.filter(filter_obj.search_key < filter_obj.search_value).all()
            elif filter_obj.comparator == 'eq':
                user_db_objs = UsersDB.query.filter(filter_obj.search_key == filter_obj.search_value).all()
            elif filter_obj.comparator == 'gt':
                user_db_objs = UsersDB.query.filter(filter_obj.search_key > filter_obj.search_value).all()

        # format output as scim objects to return to Okta
        for user in user_db_objs: 
            out.append(user.scim_user)

        return out
    
    def create_user(self, scim_user: SCIMUser) -> SCIMUser:
        # if no unique ID exists on incoming scim object, create one
        # THIS MAY NEED TO CHANGE BASED ON IMPLEMENTATION DEPENDING ON 
        # HOW THE UNIQUE IDENTIFIER IS GENERATED 
        if scim_user.id == '':
            id = str(uuid4())
        else:
            id = scim_user.id


        if LOG_LEVEL == logging.DEBUG:
            logger.debug('Creating user in DB: %s' % vars(scim_user))
        else: 
            logger.info('Creating %s in users DB' % scim_user.userName)


        # set up the database object from SCIM values, exclude custom attributes from the __init__, they can key error if null
        # MAPPINGS IMPLEMENTATION DONE HERE
        db_user = UsersDB(id=id, firstName=scim_user.givenName, lastName=scim_user.familyName, email=scim_user.email, phone=scim_user.mobilePhone, \
            password=scim_user.password, active=scim_user.active)


        # handle the custom attributes outside of the initilizer, that way if there are key errors it doesnt break the whole thing
        # MAPPINGS IMPLEMENTATION DONE HERE
        try:
            db_user.city = scim_user.custom_attributes['city']
        except KeyError:
            pass
        try:
            db_user.favorite_color = scim_user.custom_attributes['favorite_color']
        except KeyError:
            pass
        try:
            db_user.number = scim_user.custom_attributes['number']
        except KeyError:
            pass


        # update the last modified attribute on the user object to now
        # lastModified MAPPING IMPLEMENTATION HERE, IF NOT SUPPORTED THEN REMOVE
        db_user.lastModified = datetime.now()


        db.session.add(db_user)
        db.session.commit()
        if LOG_LEVEL == logging.DEBUG:
            logger.debug('User create sucessful: %s' % str(db_user))
        else:
            logger.info('%s created sucessfully' % scim_user.userName)

        
        # GROUPS IMPLEMENTATION HERE. CHANGES MAY BE NEEDED HERE DEPENDING ON THE DETAILS OF THE 
        # SQL STRUCTURE. REMOVE IF GROUPS NOT SUPPORTED
        # check if groups were sent as part of the user object and attempt assignment
        if scim_user.groups != []:
            logger.info('Attempting group assignment for %s' % scim_user.userName)
            # groups take the form of a scim resource {value: group.id, display: group.displayName}
            for group in scim_user.groups:
                # group assignments must be done through the assoication object
                user_group_assoc = UsersGroupsAssociation(user_id=id, group_id=group['value'])
                db.session.add(user_group_assoc)
            db.session.commit()
            logger.info('Groups assignment sucessful for %s' % scim_user.userName)
            # if logging in debug mode print the new users userName and the list of grups they
            # are assigned to
            if LOG_LEVEL == logging.DEBUG:
                # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
                # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
                # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
                # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
                # name= input on the Column() constructor
                new_db_user: UsersDB = UsersDB.query.filter_by(id=id).first()
                group_list: List[str] = []
                for group in new_db_user.groups:
                    group_list.append(group.displayName)
                logger.debug('%s\'s groups: %s' % (scim_user.userName, str(group_list)))


        return db_user.scim_user

    def update_user(self, scim_user: SCIMUser) -> SCIMUser:
        # we can assume they exist because a GET is always called before the update to check for existence 
        logger.info('Looking up user with ID %s in DB' % scim_user.id)
        # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
        # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
        # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
        # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
        # name= input on the Column() constructor
        user_db_object: UsersDB = UsersDB.query.filter_by(id=scim_user.id).first()


        # override existing value with values from the incoming scim object
        # MAPPINGS IMPLEMENTATION DONE HERE
        user_db_object.firstName = scim_user.givenName
        user_db_object.lastName = scim_user.familyName
        user_db_object.email = scim_user.email
        user_db_object.phone = scim_user.mobilePhone
        user_db_object.active = scim_user.active
        # if the password is not specified do nothing with it (should only be sent on activations or password updates)
        # IF PASSWORDS ARENT SUPPORTED IN YOUR CONNECTOR REMOVE THIS
        if scim_user.password != '': user_db_object.password = scim_user.password
        

        # need to check for key errors (PUTs are replcement updates so if they dont exist set them to None)
        # MAPPINGS IMPLEMENTATION DONE HERE
        try:
            user_db_object.city = scim_user.custom_attributes['city']
        except KeyError:
            user_db_object.city = None
        try:
            user_db_object.favorite_color = scim_user.custom_attributes['favorite_color']
        except KeyError:
            user_db_object.favorite_color = None
        try:
            user_db_object.number = scim_user.custom_attributes['number']
        except KeyError:
            user_db_object.number = None


        # GROUPS IMPLEMENTATION HERE, WILL NEED TO BE UPDATED ACCORDING TO HOW GROUPS ARE HANDLED
        # IN YOUR DATABASE STRUCTURE. REMOVE IF GROUPS NOT SUPPORTED
        # get the groups the user is currently assigned to
        user_groups_assoc_db_objs: List[UsersGroupsAssociation] = user_db_object.group_associations
        # if there are groups in the scim object then figure out if there are changes and make them
        if scim_user.groups != []:
            # loop through incoming groups, if its already assigned do nothing, if its not assigned
            # assign it
            for group in scim_user.groups:
                group_id = group['value']
                for group_assoc in user_groups_assoc_db_objs:
                    if group_id == group_assoc.group_id:
                        break
                else:
                    new_assoc = UsersGroupsAssociation(user_id=scim_user.id, group_id=group_id)
                    db.session.add(new_assoc)
            # loop through existing associations, if an existing association is not found in the incoming
            # group list, then remove it.
            for assoc in user_groups_assoc_db_objs:
                for group in scim_user.groups:
                    if assoc.group_id == group['value']:
                        break
                else:
                    db.session.delete(assoc)
        # if there are no groups in the incoming scim request but there are groups in the DB then
        # remove all the users group assignments in the DB
        elif scim_user.groups == [] and user_groups_assoc_db_objs is not None:
            for assoc in user_groups_assoc_db_objs:
                db.session.delete(assoc)
            

        # update the last modified attribute on the user object to now
        # lastModified MAPPING IMPLEMENTATION HERE, IF NOT SUPPORTED THEN REMOVE
        user_db_object.lastModified = datetime.now()
        

        db.session.commit()
        # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
        # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
        # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
        # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
        # name= input on the Column() constructor
        # return the updated object
        return UsersDB.query.filter_by(id=scim_user.id).first().scim_user