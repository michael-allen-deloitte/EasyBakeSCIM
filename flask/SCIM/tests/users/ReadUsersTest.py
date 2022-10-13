import requests
from logging import DEBUG
from unittest import TestCase, main
from os.path import isfile

from SCIM.helpers import set_up_logger
from SCIM.tests.common import BASE_URL, GET_ID, CACHE_DIR, LOCAL_DEPLOYMENT, TestHelper

logger = set_up_logger(__name__, level=DEBUG)

ENDPOINT_URI = '/Users'

test_helper = TestHelper(ENDPOINT_URI, logger)

class ReadUsersTests(TestCase):
    def setUp(self) -> None:
        self.assertTrue(test_helper.clear_cache())
    
    def tearDown(self) -> None:
        self.assertTrue(test_helper.clear_cache())

    def test_list_all_users(self) -> None:
        request_url = BASE_URL.strip('/') + ENDPOINT_URI
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        self.assertEqual(len(response.json()['Resources']), 22)

    def test_pagination_cache(self) -> None:
        users = []
        request_url = BASE_URL.strip('/') + '/Users?startIndex=1&count=1'
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['Resources']), 1)
        users.append(response.json())
        total_results = response.json()['totalResults']
        index = 1
        while len(users) < total_results:
            index += 1
            # cant check if these files exist when not running locally
            if LOCAL_DEPLOYMENT:
                self.assertTrue(isfile(CACHE_DIR + '/full_import_cache.json'))
                self.assertTrue(isfile(CACHE_DIR + '/full_import_cache.json.lock'))
            request_url = BASE_URL.strip('/') + '/Users?startIndex=%i&count=1&totalResults=%i' % (index, total_results)
            response = requests.get(request_url, verify=False)
            if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()['Resources']), 1)
            users.append(response.json())
        self.assertEqual(len(users), total_results)
        if LOCAL_DEPLOYMENT: self.assertFalse(isfile(CACHE_DIR + '/full_import_cache.json.lock'))

    def test_list_users_single_page(self) -> None:
        # do get all users with no params to get the total results
        request_url = BASE_URL.strip('/') + '/Users?startIndex=1&count=3'
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['Resources']), 3)
        total_results = response.json()['totalResults']
        # get the second page
        request_url = BASE_URL.strip('/') + '/Users?startIndex=4&count=2&totalResults=%i' % total_results
        response = requests.get(request_url, verify=False)
        logger.info('Second page response: %s' % response.json())
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['Resources']), 2)

    def test_get_single_user(self) -> None:
        request_url = BASE_URL.strip('/') + '/Users/' + GET_ID
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)

    def test_list_users_lt_filter(self) -> None:
        filter = '?filter=number lt 4'
        request_url = BASE_URL.strip('/') + ENDPOINT_URI + filter
        response = requests.get(request_url, verify=False)
        self.assertEqual(response.status_code, 200)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        # Expecting 3 returned users
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        self.assertEqual(len(response.json()['Resources']), 3)
    
    def test_list_users_eq_filter(self) -> None:
        filter = '?filter=active eq true'
        request_url = BASE_URL.strip('/') + ENDPOINT_URI + filter
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        self.assertEqual(len(response.json()['Resources']), 12)

    def test_list_users_gt_filter(self) -> None:
        filter = '?filter=number gt 5'
        request_url = BASE_URL.strip('/') + ENDPOINT_URI + filter
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        self.assertEqual(len(response.json()['Resources']), 17)

    def test_incremental_import(self) -> None:
        test_filter = '?filter=meta.lastModified gt \"2021-05-07T14:19:34Z\"'
        request_url = BASE_URL.strip('/') + ENDPOINT_URI + test_filter
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        self.assertEqual(len(response.json()['Resources']), 17)

    def test_incremental_pagination_cache(self) -> None:
        users = []
        request_url = BASE_URL.strip('/') + '/Users?filter=meta.lastModified gt \"2021-05-07T14:19:34Z\"&startIndex=1&count=1'
        response = requests.get(request_url, verify=False)
        if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['Resources']), 1)
        users.append(response.json())
        total_results = response.json()['totalResults']
        index = 1
        while len(users) < total_results:
            index += 1
            # cant check if these files exist when not running locally
            if LOCAL_DEPLOYMENT:
                self.assertTrue(isfile(CACHE_DIR + '/incremental_import_cache.json'))
                self.assertTrue(isfile(CACHE_DIR + '/incremental_import_cache.json.lock'))
            request_url = BASE_URL.strip('/') + '/Users?filter=meta.lastModified gt \"2021-05-07T14:19:34Z\"&startIndex=%i&count=1&totalResults=%i' % (index, total_results)
            response = requests.get(request_url, verify=False)
            if response.status_code != 200: logger.error('Response from Connector: %s' % str(response.json()))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()['Resources']), 1)
            users.append(response.json())
        self.assertEqual(len(users), total_results)
        if LOCAL_DEPLOYMENT: self.assertFalse(isfile(CACHE_DIR + '/incremental_import_cache.json.lock'))

if __name__ == '__main__':
    main()