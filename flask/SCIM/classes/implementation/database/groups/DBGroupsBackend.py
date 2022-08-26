import logging
import uuid
from typing import List
from datetime import datetime

from SCIM import db, LOG_LEVEL, LOG_FORMAT
from SCIM.classes.generic.GroupsBackend import GroupsBackend
from SCIM.classes.generic.SCIMGroup import SCIMGroup
from SCIM.classes.implementation.database.models import GroupsDB
from SCIM.classes.implementation.database.groups.DBGroupsFilter import DBGroupsFilter

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

class DBGroupsBackend(GroupsBackend):
    def get_group(self, group_id: str) -> SCIMGroup:
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

        for group in group_db_objs: 
            out.append(group.scim_group)

        return out
    
    def create_group(self, scim_group: SCIMGroup) -> SCIMGroup:
        if scim_group.id == '':
            id = str(uuid.uuid4())
        else:
            id = scim_group.id

        logger.debug('Creating group in DB: %s' % vars(scim_group))

        db_group = GroupsDB(id=id, displayName=scim_group.displayName)

        # handle the custom attributes outside of the initilizer, that way if there are key errors it doesnt break the whole thing
        try:
            db_group.description = scim_group.custom_attributes['description']
        except KeyError:
            pass

        db_group.lastModified = datetime.now()

        db.session.add(db_group)
        db.session.commit()
        logger.debug('Group create sucessful: %s' % str(db_group))
        return db_group.scim_group

    def update_group(self, scim_group: SCIMGroup) -> SCIMGroup:
        # we can assume they exist because a get is always called before the update to check for existance 
        logger.debug('Looking up group with ID %s in DB' % scim_group.id)
        group_db_object: GroupsDB = GroupsDB.query.filter_by(id=scim_group.id).first()
        group_db_object.displayName = scim_group.displayName
        
        # need to check for key errors (PUTs are replcement updates so if they dont exist set them to None)
        try:
            group_db_object.description = scim_group.custom_attributes['description']
        except KeyError:
            group_db_object.description = None
        
        group_db_object.lastModified = datetime.now()

        db.session.commit()
        return GroupsDB.query.filter_by(id=scim_group.id).first().scim_group

    def delete_group(self, group_id: str) -> None:
        logger.debug('Looking up group with ID %s in DB' % group_id)
        # if 'id' is not a string type in the DB you will need to typcast it here
        group_db_object: GroupsDB = GroupsDB.query.filter_by(id=group_id).first()
        logger.debug('Deleting group with ID %s in DB' % group_id)
        db.session.delete(group_db_object)