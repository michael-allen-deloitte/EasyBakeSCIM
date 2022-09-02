from logging import DEBUG
from unittest import TestCase, main

from SCIM.helpers import set_up_logger
from SCIM.tests.common import TestHelper

logger = set_up_logger(__name__, level=DEBUG)

test_helper = TestHelper('/Users', logger)

class CreateUserTests(TestCase):
    def test_create_user(self) -> None:
        response = test_helper.post_file_contents('../data/createNewUser.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

    def test_create_user_with_custom(self) -> None:
        response = test_helper.post_file_contents('../data/createNewUser-withCustomExtension.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())
    
    def test_create_pending(self) -> None:
        response = test_helper.post_file_contents('../data/createPendingUser.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

    def test_create_pending_with_custom(self) -> None:
        response = test_helper.post_file_contents('../data/createPendingUser-withCustomExtension.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

if __name__ == '__main__':
    main()