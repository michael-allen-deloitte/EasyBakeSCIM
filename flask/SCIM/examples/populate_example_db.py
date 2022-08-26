from datetime import datetime
from typing import List, Tuple

from SCIM import db
from SCIM.classes.implementation.database.models import UsersDB, GroupsDB, UsersGroupsAssociation

def read_user_data(in_path: str) -> List[UsersDB]:
    out = []
    with open(in_path, 'r', errors='surrogateescape') as input_file:
        for line in input_file:
            if 'firstName' in line:
                pass
            else:
                firstName, lastName, email, phone, guid, city, password, favorite_color, active, number, lastModified = line.split(',')
                db_obj = UsersDB(id=guid, firstName=firstName, lastName=lastName, email=email, phone=phone, city=city, password=password, \
                    favorite_color=favorite_color, active=active == 'true', number=int(number), lastModified=datetime.fromisoformat(lastModified.strip().strip('Z')))
                out.append(db_obj)
    return out

def read_group_data(in_path: str) -> List[GroupsDB]:
    out = []
    with open(in_path, 'r', errors='surrogateescape') as input_file:
        for line in input_file:
            if 'displayName' in line:
                pass
            else:
                id, displayName, description, lastModified = line.split(',')
                db_obj = GroupsDB(id=id, displayName=displayName, description=description, lastModified=datetime.fromisoformat(lastModified.strip().strip('Z')))
                out.append(db_obj)
    return out

def read_group_membership_data(in_path: str) -> List[UsersGroupsAssociation]:
    out = []
    with open(in_path, 'r', errors='surrogateescape') as input_file:
        for line in input_file:
            if 'groupId' in line:
                pass
            else:
                group_id, user_id = line.split(',')
                db_obj = UsersGroupsAssociation(user_id = user_id, group_id = group_id)
                out.append(db_obj)
    return out

def populate_user_groups(users: List[UsersDB], groups: List[GroupsDB], group_memberships: List[UsersGroupsAssociation]) -> Tuple[List[UsersDB], List[GroupsDB]]:
    users_out = []
    groups_out = []
    for user in users:
        groups = []
        for group_association in group_memberships:
            if user.id == group_association.user_id:
                for group in groups:
                    if group.id == group_association.group_id:
                        groups.append(group)
        user.groups = groups
        users_out.append(user)
    for group in groups:
        users = []
        for user_association in group_memberships:
            if group.id == user_association.group_id:
                for user in users:
                    if user.id == user_association.user_id:
                        users.append(user)
        group.members = users
        groups_out.append(group)
    return (users_out, groups_out)
    

def generate_example_database(user_in_path: str, group_in_path: str, group_membership_in_path: str):
    user_db_objs = read_user_data(user_in_path)
    group_db_objs = read_group_data(group_in_path)
    group_membership_objs = read_group_membership_data(group_membership_in_path)
    user_db_objs, group_db_objs = populate_user_groups(user_db_objs, group_db_objs, group_membership_objs)
    for db_obj in user_db_objs:
        db.session.add(db_obj)
    db.session.commit()
    for db_obj in group_db_objs:
        db.session.add(db_obj)
    db.session.commit()
    for db_obj in group_membership_objs:
        db.session.add(db_obj)
    db.session.commit()