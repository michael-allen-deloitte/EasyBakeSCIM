from SCIM import db
from SCIM.classes.generic.SCIMUser import SCIMUser

# https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/

class UsersDB(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(50), primary_key=True, unique=True)
    firstName = db.Column(db.String(30), nullable=False)
    lastName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    city = db.Column(db.String(25), nullable=True)
    password = db.Column(db.String(30), nullable=False)
    favorite_color = db.Column(db.String(10), nullable=True)
    active = db.Column(db.Boolean, nullable=False)
    number = db.Column(db.Interger, nullable=True)

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
            # in a real implementation you would want to exclude this
            'password': self.password,
            'favorite_color': self.favorite_color,
            'active': self.active
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
            # in a real implementation you would want to exclude this
            'password': self.password,
            'favorite_color': self.favorite_color,
            'active': self.active
        }
        return 'UsersDB<%s>' % str(out)