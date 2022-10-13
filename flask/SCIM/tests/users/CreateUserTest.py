from logging import DEBUG
from unittest import TestCase, main
from requests import get

from SCIM.helpers import set_up_logger
from SCIM.tests.common import TestHelper, BASE_URL

logger = set_up_logger(__name__, level=DEBUG)

test_helper = TestHelper('/Users', logger)

class CreateUserTests(TestCase):
    def test_create_user(self) -> None:
        response = test_helper.post_file_contents('../data/createNewUser.json')
        if response.status_code != 201: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 201)
        try:
            if response.json()['id'] == '': logger.error('Response from Connector: %s' % str(response.json()))
        except KeyError:
            logger.error('Response from Connector: %s' % str(response.json()))
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

    def test_create_user_with_custom(self) -> None:
        response = test_helper.post_file_contents('../data/createNewUser-withCustomExtension.json')
        if response.status_code != 201: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 201)
        try:
            if response.json()['id'] == '': logger.error('Response from Connector: %s' % str(response.json()))
        except KeyError:
            logger.error('Response from Connector: %s' % str(response.json()))
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())
    
    def test_create_pending(self) -> None:
        response = test_helper.post_file_contents('../data/createPendingUser.json')
        if response.status_code != 201: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 201)
        try:
            if response.json()['id'] == '':
                logger.error('Response from Connector: %s' % str(response.json()))
        except KeyError:
            logger.error('Response from Connector: %s' % str(response.json()))
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

    def test_create_pending_with_custom(self) -> None:
        response = test_helper.post_file_contents('../data/createPendingUser-withCustomExtension.json')
        if response.status_code != 201: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 201)
        try:
            if response.json()['id'] == '':
                logger.error('Response from Connector: %s' % str(response.json()))
        except KeyError:
            logger.error('Response from Connector: %s' % str(response.json()))
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

    def test_create_user_with_groups(self) -> None:
        response = test_helper.post_file_contents('../data/createNewUser-withGroups.json')
        if response.status_code != 201: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 201)
        try:
            if response.json()['id'] == '': logger.error('Response from Connector: %s' % str(response.json()))
        except KeyError:
            logger.error('Response from Connector: %s' % str(response.json()))
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        user_id = response.json()['id']
        if len(response.json()['groups']) != 1: logger.error('Response from connector: %s' % response.json())
        self.assertEqual(len(response.json()['groups']), 1)
        group_id = response.json()['groups'][0]['value']
        groups_response = get(BASE_URL + '/Groups/' + group_id)
        if groups_response.status_code != 200: logger.error('Groups Response from connector: %s' % groups_response.json())
        self.assertEqual(groups_response.status_code, 200)
        members = groups_response.json()['members']
        new_user_in_group = False
        for member in members:
            if member['value'] == user_id:
                new_user_in_group = True
                break
        else:
            logger.error('New user not found in members of group they were supposed to be assigned to')
        self.assertTrue(new_user_in_group)
        logger.info('The user returned from the connector: %s' % response.json())

if __name__ == '__main__':
    main()