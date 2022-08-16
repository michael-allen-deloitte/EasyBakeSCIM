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

logger.info("These tests use the sample data in SCIM/examples/users.csv and expect a flushed db")

config = configparser.ConfigParser()
config_path = './tests.ini'
if os.path.exists(config_path):
    config.read(config_path)
else:
    print('Could not read config file from path %s' % config_path)
    sys.exit(1)

BASE_URL = config['Local Deployment']['base_url']

def put_file_contents(file_path: str) -> requests.Response:
    with open(file_path, 'r') as data_file:
        test_data = json.load(data_file)
    request_url = BASE_URL.strip('/') + '/Users/' + test_data['id']
    logger.info('Making PUT to %s' % request_url)
    return requests.put(request_url, json=test_data, verify=False)

class UpdateUserTests(unittest.TestCase):
    def test_activate_user(self):
        response = put_file_contents('./data/activateUser.json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['active'])
        logger.info('User status returned as active')
        logger.info('The user returned from the connector: %s' % response.json())

    def test_profile_update(self):
        response = put_file_contents('./data/pushProfileUpdate.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name']['givenName'], 'Dana1')
        self.assertEqual(response.json()['name']['familyName'], 'Ruiz1')
        logger.info('User attributes updated successfully')
        logger.info('The user returned from the connector: %s' % response.json())

    def test_password_update(self):
        response = put_file_contents('./data/pushPasswordUpdate.json')
        self.assertEqual(response.status_code, 200)
        logger.info('User password updated successfully')
        logger.info('The user returned from the connector: %s' % response.json())

    def test_deactivate_user(self):
        response = put_file_contents('./data/deactivateUser.json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['active'])
        logger.info('User status returned as deactivated')
        logger.info('The user returned from the connector: %s' % response.json())

def suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTest(UpdateUserTests('test_activate_user'))
    suite.addTest(UpdateUserTests('test_profile_update'))
    suite.addTest(UpdateUserTests('test_password_update'))
    suite.addTest(UpdateUserTests('test_deactivate_user'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())