from logging import DEBUG
from unittest import TestCase, main
from requests import delete

from SCIM.helpers import set_up_logger
from SCIM.tests.common import TestHelper, BASE_URL

logger = set_up_logger(__name__, level=DEBUG)

ENDPOINT_URI = '/Groups'

test_helper = TestHelper(ENDPOINT_URI, logger)

logger.info("These tests use the sample data in SCIM/examples/group-no-members.csv and and expect a flushed db")

class DeleteGroupsTests(TestCase):
    def test_delete_group(self) -> None:
        response = delete(BASE_URL + ENDPOINT_URI + '/')
        if response.status_code != 204: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 204)
        logger.info('Group with ID %s was deleted successfully')


if __name__ == '__main__':
    main()