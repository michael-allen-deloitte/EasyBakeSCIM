from SCIM import db
from SCIM.classes.implementation.database.models import UsersDB

def read_data(in_path):
    out = []
    with open(in_path, 'r', errors='surrogateescape') as input_file:
        for line in input_file:
            if line[0] == 'firstName':
                pass
            else:
                firstName, lastName, email, phone, guid, city, password, favorite_color, active = line.split(',')
                db_obj = UsersDB(id=guid, firstName=firstName, lastName=lastName, email=email, phone=phone, city=city, password=password, \
                    favorite_color=favorite_color, active=active == 'true')
                out.append(db_obj)
    return out

def generate_example_database(in_path):
    db.create_all()
    user_db_objs = read_data(in_path)
    for db_obj in user_db_objs:
        db.session.add(db_obj)
    db.session.commit()