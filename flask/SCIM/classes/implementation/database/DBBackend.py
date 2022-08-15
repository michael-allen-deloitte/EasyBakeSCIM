import logging
import uuid
from typing import List

from SCIM import db, LOG_LEVEL, LOG_FORMAT
from SCIM.classes.generic.Backend import UserBackend
from SCIM.classes.generic.SCIMUser import SCIMUser
from SCIM.classes.implementation.database.models import UsersDB
from SCIM.classes.implementation.filters.CustomFilter import CustomFilter

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

class DBBackend(UserBackend):
    def get_user(self, user_id: str) -> SCIMUser:
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

        if filter is None:
            user_db_objs = UsersDB.query.all()
        else:
            filter_obj = CustomFilter(filter)


            if filter_obj.comparator == 'lt':
                user_db_objs = UsersDB.query.filter(filter_obj.search_key < filter_obj.search_value).all()
            elif filter_obj.comparator == 'eq':
                user_db_objs = UsersDB.query.filter(filter_obj.search_key == filter_obj.search_value).all()
            elif filter_obj.comparator == 'gt':
                user_db_objs = UsersDB.query.filter(filter_obj.search_key > filter_obj.search_value).all()

        for user in user_db_objs: 
            out.append(user.scim_user)

        return out
    
    def create_user(self, scim_user: SCIMUser) -> SCIMUser:
        if scim_user.id == '':
            id = str(uuid.uuid4())
        else:
            id = scim_user.id

        logger.debug('Creating user in DB: %s' % vars(scim_user))

        db_user = UsersDB(id=id, firstName=scim_user.givenName, lastName=scim_user.familyName, email=scim_user.email, phone=scim_user.mobilePhone, \
            password=scim_user.password, active=scim_user.active)

        # handle the custom attributes outside of the initilizer, that way if there are key errors it doesnt break the whole thing
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

        db.session.add(db_user)
        db.session.commit()
        logger.debug('User create sucessful: %s' % str(db_user))
        return db_user.scim_user

    def update_user(self, scim_user: SCIMUser) -> SCIMUser:
        # we can assume they exist because a get is always called before the update to check for existance 
        logger.debug('Looking up user with ID %s in DB' % scim_user.id)
        user_db_object = UsersDB.query.filter_by(id=scim_user.id).first()
        user_db_object.firstName = scim_user.givenName
        user_db_object.lastName = scim_user.familyName
        user_db_object.email = scim_user.email
        user_db_object.phone = scim_user.mobilePhone
        # if the password is not specified do nothing with it (should only be sent on activations or password updates)
        if scim_user.password != '': user_db_object.password = scim_user.password
        # need to check for key errors (PUTs are replcement updates so if they dont exist set them to None)
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
        user_db_object.active = scim_user.active
        db.session.commit()
        return UsersDB.query.filter_by(id=scim_user.id).first().scim_user