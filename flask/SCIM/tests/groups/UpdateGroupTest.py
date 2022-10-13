from logging import DEBUG
from unittest import TestCase, main

from SCIM.helpers import set_up_logger
from SCIM.tests.common import TestHelper

logger = set_up_logger(__name__, level=DEBUG)

ENDPOINT_URI = '/Groups'

test_helper = TestHelper(ENDPOINT_URI, logger)

logger.info("These tests use the sample data in SCIM/examples/group-no-members.csv and and expect a flushed db")

class UpdateGroupTests(TestCase):
    def test_update_group(self) -> None:
        response = test_helper.put_file_contents('../data/updateGroup.json')
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        if response.json()['diplayName'] != 'AppGroup-Changed': logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.json()['diplayName'], 'AppGroup-Changed')
        logger.info('Group Name has been changed')

if __name__ == '__main__':
    main()