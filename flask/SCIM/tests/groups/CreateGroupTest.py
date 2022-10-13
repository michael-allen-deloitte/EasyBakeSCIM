from logging import DEBUG
from unittest import TestCase, main
from requests import get

from SCIM.helpers import set_up_logger
from SCIM.tests.common import TestHelper, BASE_URL

logger = set_up_logger(__name__, level=DEBUG)

ENDPOINT_URI = '/Groups'

test_helper = TestHelper(ENDPOINT_URI, logger)

class CreateGroupsTests(TestCase):
    def test_create_group(self) -> None:
        response = test_helper.post_file_contents('../data/createGroup.json')
        if response.status_code != 201: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 201)
        try:
            if response.json()['id'] == '': logger.error('Response from Connector: %s' % str(response.json()))
        except KeyError:
            logger.error('Response from Connector: %s' % str(response.json()))
        self.assertTrue(response.json()['id'] != '')
        group_id = response.json()['id']
        logger.info('The externalID of the returned group is %s' % group_id)
        try:
            group_members = response.json()['members']
            if len(group_members) != 2: logger.error('The returned group had an incorrect number of members: %s' % response.json())
        except KeyError:
            logger.error('The returned group had no members key: %s' % response.json())
        self.assertEqual(len(group_members), 2)
        # check each user object and make sure the group shows up there too
        for member in group_members:
            user_response = get(BASE_URL + '/Users/' + member['value'])
            if user_response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
            self.assertEqual(user_response.status_code, 200)
            user_in_group = False
            try:
                for group in user_response.json()['groups']:
                    if group['value'] == group_id:
                        user_in_group = True
                        break
                else:
                    logger.error('The group with ID %s was not found on user object with ID %s' % (group_id, member['value']))
                self.assertTrue(user_in_group)
            except KeyError:
                logger.error('User object with ID %s has no groups key' % member['value'])

        logger.info('The group returned from the connector: %s' % response.json())


if __name__ == '__main__':
    main()