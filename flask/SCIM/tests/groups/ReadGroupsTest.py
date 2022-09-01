import requests
from logging import DEBUG
from unittest import TestCase, main

from SCIM.helpers import set_up_logger
from SCIM.tests.common import BASE_URL, TestHelper

logger = set_up_logger(__name__, level=DEBUG)

ENDPOINT_URI = '/Groups'

test_helper = TestHelper(ENDPOINT_URI, logger)

class ReadGroupsTests(TestCase):
    def setUp(self) -> None:
        self.assertTrue(test_helper.clear_cache())
    
    def tearDown(self) -> None:
        self.assertTrue(test_helper.clear_cache())

    def test_list_all_groups(self):
        request_url = BASE_URL.strip('/') + ENDPOINT_URI
        response = requests.get(request_url, verify=False)
        if response.status_code != 200:
            logger.info('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        logger.info('%i Groups returned from Connector' % len(response.json()['Resources']))
        self.assertEqual(len(response.json()['Resources']), 5)


if __name__ == '__main__':
    main()