import requests
import unittest
import configparser
import os, sys
import json
import logging

LOG_LEVEL = logging.INFO
LOG_FORMAT = logging.Formatter('%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)


config = configparser.ConfigParser()
config_path = './tests.ini'
if os.path.exists(config_path):
    config.read(config_path)
else:
    print('Could not read config file from path %s' % config_path)
    sys.exit(1)

BASE_URL = config['Local Deployment']['base_url']
GET_ID = config['Local Deployment']['get_id']

class ReadUsersTests(unittest.TestCase):
    def setUp(self) -> None:
        cache_dir = config['Cache']['dir']
        if os.path.exists(cache_dir):
            cache_files = os.listdir(cache_dir)
            if len(cache_files) > 0:
                logger.info('Cleaning up any existing cache')
                for file in cache_files:
                    os.remove(os.path.join(cache_dir, file))

    def test_list_all_users(self):
        request_url = BASE_URL.strip('/') + '/Users'
        response = requests.get(request_url)
        self.assertEqual(response.status_code, 200)
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        logger.info('Response from Connector: %s' % str(response.json()))

    def test_pagination_cache(self):
        users = []
        request_url = BASE_URL.strip('/') + '/Users?startIndex=1&count=1'
        response = requests.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['Resources']), 1)
        users.append(response.json())
        total_results = response.json()['totalResults']
        index = 1
        while len(users) < total_results:
            index += 1
            self.assertTrue(os.path.isfile('../.cache/list_users.json'))
            self.assertTrue(os.path.isfile('../.cache/list_users.json.lock'))
            request_url = BASE_URL.strip('/') + '/Users?startIndex=%i&count=1&totalResults=%i' % (index, total_results)
            response = requests.get(request_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()['Resources']), 1)
            users.append(response.json())
        self.assertFalse(os.path.isfile('../.cache/list_users.json.lock'))

    def test_list_users_single_page(self):
        # do get all users with no params to get the total results
        request_url = BASE_URL.strip('/') + '/Users?startIndex=1&count=3'
        response = requests.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['Resources']), 3)
        total_results = response.json()['totalResults']
        # get the second page
        request_url = BASE_URL.strip('/') + '/Users?startIndex=4&count=2&totalResults=%i' % total_results
        response = requests.get(request_url)
        logger.info('Second page response: %s' % response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['Resources']), 2)

    def test_get_single_user(self):
        request_url = BASE_URL.strip('/') + '/Users/' + GET_ID
        response = requests.get(request_url)
        logger.info(response.json())
        self.assertEqual(response.status_code, 200)
        logger.info('Response from Connector: %s' % str(response.json()))

    def test_list_users_lt_filter(self):
        filter = '?filter=number lt 4'
        request_url = BASE_URL.strip('/') + '/Users' + filter
        response = requests.get(request_url)
        self.assertEqual(response.status_code, 200)
        # Expecting 3 returned users
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        logger.info('Response from Connector: %s' % str(response.json()))
    
    def test_list_users_eq_filter(self):
        filter = '?filter=active eq true'
        request_url = BASE_URL.strip('/') + '/Users' + filter
        response = requests.get(request_url)
        self.assertEqual(response.status_code, 200)
        # Expecting 4 returned users
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        logger.info('Response from Connector: %s' % str(response.json()))

    def test_list_users_gt_filter(self):
        filter = '?filter=number gt 5'
        request_url = BASE_URL.strip('/') + '/Users' + filter
        response = requests.get(request_url)
        self.assertEqual(response.status_code, 200)
        # Expecting 3 returned users
        logger.info('%i Users returned from Connector' % len(response.json()['Resources']))
        logger.info('Response from Connector: %s' % str(response.json()))


if __name__ == '__main__':
    unittest.main()