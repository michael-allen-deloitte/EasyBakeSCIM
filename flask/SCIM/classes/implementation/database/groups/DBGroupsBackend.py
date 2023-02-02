import logging
import uuid
from typing import List
from datetime import datetime

from SCIM import db
from SCIM.helpers import set_up_logger, LOG_LEVEL
from SCIM.classes.generic.GroupsBackend import GroupsBackend
from SCIM.classes.generic.SCIMGroup import SCIMGroup
from SCIM.classes.implementation.database.models import GroupsDB, UsersGroupsAssociation
from SCIM.classes.implementation.database.groups.DBGroupsFilter import DBGroupsFilter

logger = set_up_logger(__name__)

class DBGroupsBackend(GroupsBackend):
    def get_group(self, group_id: str) -> SCIMGroup:
        # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
        # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
        # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
        # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
        # name= input on the Column() constructor
        group_db_object: List[GroupsDB] = GroupsDB.query.filter_by(id=group_id).all()


        if len(group_db_object) > 1:
            logger.error('More than 1 object was found with the id:%s' % group_id)
            raise(LookupError, 'More than 1 object was found with the id:%s' % group_id)
        elif len(group_db_object) == 0:
            return None
        else:
            return group_db_object[0].scim_group

    def list_groups(self, filter: str = None) -> List[SCIMGroup]:
        out: List[SCIMGroup] = []
        group_db_objs: List[GroupsDB] = []

        # Check for filter, create one if needed, and query the groups
        if filter is None:
            group_db_objs: List[GroupsDB] = GroupsDB.query.all()
        else:
            filter_obj = DBGroupsFilter(filter)
            if filter_obj.comparator == 'lt':
                group_db_objs = GroupsDB.query.filter(filter_obj.search_key < filter_obj.search_value).all()
            elif filter_obj.comparator == 'eq':
                group_db_objs = GroupsDB.query.filter(filter_obj.search_key == filter_obj.search_value).all()
            elif filter_obj.comparator == 'gt':
                group_db_objs = GroupsDB.query.filter(filter_obj.search_key > filter_obj.search_value).all()

        # format output as scim objects to return to Okta
        for group in group_db_objs: 
            out.append(group.scim_group)

        return out
    
    def create_group(self, scim_group: SCIMGroup) -> SCIMGroup:
        # if no unique ID exists on incoming scim object, create one
        # THIS MAY NEED TO CHANGE BASED ON IMPLEMENTATION DEPENDING ON 
        # HOW THE UNIQUE IDENTIFIER IS GENERATED 
        if scim_group.id == '':
            id = str(uuid.uuid4())
        else:
            id = scim_group.id

        if LOG_LEVEL == logging.DEBUG:
            logger.debug('Creating group in DB: %s' % vars(scim_group))
        else:
            logger.info('Creating %s in groups DB' % scim_group.displayName)

        # set up the database object from SCIM values, exclude custom attributes from the __init__, they can key error if null
        # MAPPINGS IMPLEMENTATION DONE HERE
        db_group = GroupsDB(id=id, displayName=scim_group.displayName)


        # handle the custom attributes outside of the initilizer, that way if there are key errors it doesnt break the whole thing
        # MAPPINGS IMPLEMENTATION DONE HERE
        try:
            db_group.description = scim_group.custom_attributes['description']
        except KeyError:
            pass


        # update the last modified attribute on the group object to now
        # lastModified MAPPING IMPLEMENTATION HERE, IF NOT SUPPORTED THEN REMOVE
        db_group.lastModified = datetime.now()


        db.session.add(db_group)
        db.session.commit()
        if LOG_LEVEL == logging.DEBUG:
            logger.debug('Group create sucessful: %s' % str(db_group))
        else:
            logger.info('%s created successfully' % scim_group.displayName)

        # MAPPING IMPLEMENTATION HERE, THIS LOGIC MAY NEED TO CHANGE DEPENDING ON YOUR SQL STRUCTURE
        # if the group has members to create with...
        if scim_group.members != []:
            logger.info('Attempting to assign %s to %i users' % (scim_group.displayName, len(scim_group.members)))
            # users take the form of {value: user.id, display: some attribute that doesnt matter}
            for user in scim_group.members:
                # group assignments have to be done through the associatio object
                assoc = UsersGroupsAssociation(user_id=user['value'], group_id=id)
                db.session.add(assoc)
            db.session.commit()
            logger.info('%i users successfully assigned to %s' % (len(scim_group.members), scim_group.displayName))
            # if in debug mode print a statement with the new groups name as well as a list of the members
            if LOG_LEVEL == logging.DEBUG:
                # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
                # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
                # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
                # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
                # name= input on the Column() constructor
                new_db_group: GroupsDB = GroupsDB.query.filter_by(id=id).first()
                members_list: List[str] = []
                for user in new_db_group.members:
                    members_list.append(user.scim_user.userName)
                logger.debug('%s\'s members: %s' % (scim_group.displayName, str(members_list)))


        return db_group.scim_group

    def update_group(self, scim_group: SCIMGroup) -> SCIMGroup:
        # we can assume they exist because a get is always called before the update to check for existance 
        logger.debug('Looking up group with ID %s in DB' % scim_group.id)
        # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
        # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
        # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
        # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
        # name= input on the Column() constructor
        group_db_object: GroupsDB = GroupsDB.query.filter_by(id=scim_group.id).first()


        group_db_object.displayName = scim_group.displayName
        

        # need to check for key errors (PUTs are replcement updates so if they dont exist set them to None)
        # MAPPINGS IMPLEMENTATION DONE HERE (if custom attributes beyond description)
        try:
            group_db_object.description = scim_group.custom_attributes['description']
        except KeyError:
            group_db_object.description = None


        # IMPLEMENTATION MAY CHANGE HERE DEPEDING ON YOUR SQL STRUCTURE
        # get the users that are currently members of the group
        user_groups_assoc_db_objs: List[UsersGroupsAssociation] = group_db_object.member_associations
        # if the incoming scim object has members, figure out if there is a delta and make changes
        if scim_group.members != []:
            # loop through incoming users, if they are already part of the group do nothing, if not
            # then add them
            for user in scim_group.members:
                for assoc in user_groups_assoc_db_objs:
                    if user['value'] == assoc.user_id:
                        break
                else:
                    new_assoc = UsersGroupsAssociation(user_id=user['value'], group_id=scim_group.id)
                    db.session.add(new_assoc)
            # loop through existing users, if the dont exist in the incoming object remove them from the group.
            # All updates are PUT, so the old object is replace with the new one
            for assoc in user_groups_assoc_db_objs:
                for user in scim_group.members:
                    if user['value'] == assoc.user_id:
                        break
                else:
                    db.session.delete(assoc)
            # if there are no members in the incoming scim object but there are existing members in the db 
            # then remove all existing members in the db
        elif scim_group.members == [] and user_groups_assoc_db_objs is not None:
            for assoc in user_groups_assoc_db_objs:
                db.session.delete(assoc)


        # update the last modified attribute on the group object to now
        # lastModified MAPPING IMPLEMENTATION HERE, IF NOT SUPPORTED THEN REMOVE
        group_db_object.lastModified = datetime.now()


        db.session.commit()
        # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
        # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
        # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
        # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
        # name= input on the Column() constructor
        return GroupsDB.query.filter_by(id=scim_group.id).first().scim_group

    def delete_group(self, group_id: str) -> None:
        logger.info('Looking up group with ID %s in DB' % group_id)
        # BELOW LINE MAY NEED CHANGES DEPENDING ON IMPLEMENTATION AND HOW THE 
        # OBJECT WAS SET UP IN models.py. IF NOT USING 'id' AS THE UNIQUE IDENTIFIER
        # COLUMN THEN IT WILL NEED TO BE CHANGED. NOTE THE ATTRIBUTE CAN BE NAMED
        # 'id' ON THE DB OBJECT AND MAPPED TO A DIFFERENT COLUMN NAME VIA THE 
        # name= input on the Column() constructor
        # if 'id' is not a string type in the DB you will need to typcast it here
        group_db_object: GroupsDB = GroupsDB.query.filter_by(id=group_id).first()
        # IMPLEMENTATION CHANGES HERE, UPDATES MAY BE REQUIRED DEPENDING ON SQL STRUCTURE
        association_db_objects: List[UsersGroupsAssociation] = UsersGroupsAssociation.query.filter_by(group_id=group_id).all()


        # IMPLEMENTATION CHANGES HERE, UPDATES MAY BE REQUIRED DEPENDING ON SQL STRUCTURE
        # deleteing the associations before the group
        logger.info('Deleting user associations for group with ID %s' % group_id)
        for association in association_db_objects:
            db.session.delete(association)
        # if something was deleted then commit the changes before deleting the group
        if len(association_db_objects) != 0:
            db.session.commit()


        logger.info('Deleting group with ID %s in DB' % group_id)
        db.session.delete(group_db_object)
        db.session.commit()