import logging
import uuid

from SCIM import db, logger
from SCIM.classes.generic.Backend import UserBackend
from SCIM.classes.generic.SCIMUser import SCIMUser
from SCIM.classes.implementation.database.models import UsersDB

class DBBackend(UserBackend):
    def get_user(self, user_id: str) -> SCIMUser:
        user_db_object = UsersDB.query.filter_by(id=user_id).all()
        if len(user_db_object) > 1:
            logger.error('More than 1 object was found with the id:%s' % user_id)
            raise(LookupError, 'More than 1 object was found with the id:%s' % user_id)
        elif len(user_db_object) == 0:
            return None
        else:
            return user_db_object[0].scim_user
    
    def create_user(self, scim_user: SCIMUser) -> SCIMUser:
        if scim_user.id == '':
            id = str(uuid.uuid4())
        else:
            id = scim_user.id

        logger.debug('Creating user in DB: %s' % vars(scim_user))

        db_user = UsersDB(id=id, firstName=scim_user.givenName, lastName=scim_user.familyName, email=scim_user.email, phone=scim_user.mobilePhone, \
            city=scim_user.custom_attributes['city'], password=scim_user.password, favorite_color=scim_user.custom_attributes['favorite_color'], active=scim_user.active)
        
        db.session.add(db_user)
        db.session.commit()
        logger.debug('User create sucessful')
        return db_user.scim_user

    def update_user(self, scim_user: SCIMUser) -> SCIMUser:
        user_db_object = UsersDB.query.filter_by(id=scim_user.id).first()
        user_db_object.firstName = scim_user.givenName
        user_db_object.lastName = scim_user.familyName
        user_db_object.email = scim_user.email
        user_db_object.phone = scim_user.mobilePhone
        user_db_object.city = scim_user.custom_attributes['city']
        user_db_object.password = scim_user.password
        user_db_object.favorite_color = scim_user.custom_attributes['favorite_color']
        user_db_object.active = scim_user.active
        db.session.commit()
        return UsersDB.query.filter_by(id=scim_user.id).first().scim_user