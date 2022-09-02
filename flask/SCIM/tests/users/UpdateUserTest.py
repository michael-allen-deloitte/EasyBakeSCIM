from logging import DEBUG
from unittest import TestCase, TestSuite, TextTestRunner

from SCIM.helpers import set_up_logger
from SCIM.tests.common import TestHelper

logger = set_up_logger(__name__, level=DEBUG)

test_helper = TestHelper('/Users', logger)

logger.info("These tests use the sample data in SCIM/examples/users.csv and expect a flushed db")

class UpdateUserTests(TestCase):
    def test_activate_user(self) -> None:
        response = test_helper.put_file_contents('../data/activateUser.json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['active'])
        logger.info('User status returned as active')
        logger.info('The user returned from the connector: %s' % response.json())

    def test_profile_update(self) -> None:
        response = test_helper.put_file_contents('../data/pushProfileUpdate.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name']['givenName'], 'Dana1')
        self.assertEqual(response.json()['name']['familyName'], 'Ruiz1')
        logger.info('User attributes updated successfully')
        logger.info('The user returned from the connector: %s' % response.json())

    def test_password_update(self) -> None:
        response = test_helper.put_file_contents('../data/pushPasswordUpdate.json')
        self.assertEqual(response.status_code, 200)
        logger.info('User password updated successfully')
        logger.info('The user returned from the connector: %s' % response.json())

    def test_deactivate_user(self) -> None:
        response = test_helper.put_file_contents('../data/deactivateUser.json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['active'])
        logger.info('User status returned as deactivated')
        logger.info('The user returned from the connector: %s' % response.json())

def suite() -> TestSuite:
    suite = TestSuite()
    suite.addTest(UpdateUserTests('test_activate_user'))
    suite.addTest(UpdateUserTests('test_profile_update'))
    suite.addTest(UpdateUserTests('test_password_update'))
    suite.addTest(UpdateUserTests('test_deactivate_user'))
    return suite

if __name__ == '__main__':
    runner = TextTestRunner()
    runner.run(suite())