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

def post_file_contents(file_path: str) -> requests.Response:
    with open(file_path, 'r') as data_file:
        test_data = json.load(data_file)
    request_url = BASE_URL.strip('/') + '/Users'
    logger.info('Making POST to %s' % request_url)
    return requests.post(request_url, json=test_data, verify=False)

class CreateUserTests(unittest.TestCase):
    def test_create_user(self):
        response = post_file_contents('./data/createNewUser.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

    def test_create_user_with_custom(self):
        response = post_file_contents('./data/createNewUser-withCustomExtension.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())
    
    def test_create_pending(self):
        response = post_file_contents('./data/createPendingUser.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

    def test_create_pending_with_custom(self):
        response = post_file_contents('./data/createPendingUser-withCustomExtension.json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['id'] != '')
        logger.info('The externalID of the returned user is %s' % response.json()['id'])
        logger.info('The user returned from the connector: %s' % response.json())

if __name__ == '__main__':
    unittest.main()