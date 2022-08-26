from sqlalchemy.sql.schema import Column, ForeignKey

from SCIM import db
from SCIM.classes.generic.SCIMUser import SCIMUser
from SCIM.classes.generic.SCIMGroup import SCIMGroup

# https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/

class UsersDB(db.Model):
    __tablename__ = 'users'
    # Set variable names to be what Okta will send them over as, and map to 
    # the DB column via the 'name' argument. If it is not done this way
    # the filter objects will not work properly
    id = db.Column(db.String(50), primary_key=True, unique=True, name='id')
    firstName = db.Column(db.String(50), nullable=False, name='firstName')
    lastName = db.Column(db.String(50), nullable=False, name='lastName')
    email = db.Column(db.String(100), nullable=False, name='email')
    phone = db.Column(db.String(15), nullable=True, name='phone')
    city = db.Column(db.String(50), nullable=True, name='city')
    password = db.Column(db.String(50), nullable=False, name='password')
    favorite_color = db.Column(db.String(10), nullable=True, name='favorite_color')
    active = db.Column(db.Boolean, nullable=False, name='active')
    number = db.Column(db.Integer, nullable=True, name='number')
    lastModified = db.Column(db.DateTime, nullable=True, name='lastModified')
    # https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#association-object
    groups = db.relationship('UsersGroupsAssociation', back_populates='group')

    @property
    def scim_user(self) -> SCIMUser:
        scim_user_create_dict = {
            'id': self.id,
            'active': self.active,
            'userName': self.email,
            'email': self.email,
            'givenName': self.firstName,
            'familyName':self.lastName,
            'mobilePhone': self.phone,
            'password': self.password,
            'custom_attributes': {
                'city': self.city,
                'favorite_color': self.favorite_color,
                'number': self.number
            }
        }
        return SCIMUser(scim_user_create_dict, init_type='backend')

    def __repr__(self) -> str:
        out = {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'phone': self.phone,
            'city': self.city,
            # in a real implementation you would want to exclude the password
            #'password': self.password,
            'favorite_color': self.favorite_color,
            'active': self.active,
            'lastModified': self.lastModified
        }
        return 'UsersDB<%s>' % str(out)

    def __str__(self) -> str:
        out = {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'phone': self.phone,
            'city': self.city,
            # in a real implementation you would want to exclude the password
            #'password': self.password,
            'favorite_color': self.favorite_color,
            'active': self.active,
            'lastModified': self.lastModified
        }
        return 'UsersDB<%s>' % str(out)

class GroupsDB(db.Model):
    __tablename__ = 'groups'
    # Set variable names to be what Okta will send them over as, and map to 
    # the DB column via the 'name' argument. If it is not done this way
    # the filter objects will not work properly
    id = db.Column(db.String(255), primary_key=True, unique=True, name='id')
    displayName = db.Column(db.String(100), nullable=False, name='displayName')
    description = db.Column(db.String(1024), nullable=False, name='description')
    # https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#association-object
    members = db.relationship('UsersGroupsAssociation', back_populates='user')
    lastModified = db.Column(db.DateTime, nullable=True, name='lastModified')

    @property
    def scim_group(self) -> SCIMGroup:
        scim_group_create_dict = {
            'id': self.id,
            'displayName': self.displayName,
            'custom_attributes': {
                'description': self.description
            }
        }
        return SCIMGroup(scim_group_create_dict, init_type='backend')

    def __repr__(self) -> str:
        out = {
            'id': self.id,
            'displayName': self.displayName,
            'description': self.description,
            'lastModified': self.lastModified
        }
        return 'GroupsDB<%s>' % str(out)

    def __str__(self) -> str:
        out = {
            'id': self.id,
            'displayName': self.displayName,
            'description': self.description,
            'lastModified': self.lastModified
        }
        return 'GroupsDB<%s>' % str(out)

# https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#association-object
class UsersGroupsAssociation(db.Model):
    __tablename__ = 'users_groups_association'
    user_id = Column('user_id', ForeignKey('users.id'), primary_key=True)
    group_id = Column('group_id', ForeignKey('groups.id'), primary_key=True)
    user = db.relationship('UsersDB', back_populates='groups')
    group = db.relationship('GroupsDB', back_populates='members')