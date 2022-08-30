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

BASE_URL = config['Deployment']['base_url']

def post_file_contents(file_path: str) -> requests.Response:
    with open(file_path, 'r') as data_file:
        test_data = json.load(data_file)
    request_url = BASE_URL.strip('/') + '/Groups'
    logger.info('Making POST to %s' % request_url)
    return requests.post(request_url, json=test_data, verify=False)

class GroupsTests(unittest.TestCase):
    def test_list_all_groups(self):
        request_url = BASE_URL.strip('/') + '/Groups'
        response = requests.get(request_url, verify=False)
        if response.status_code != 200:
            logger.info('Response from Connector: %s' % str(response.json()))
        self.assertEqual(response.status_code, 200)
        logger.info('%i Groups returned from Connector' % len(response.json()['Resources']))
        self.assertEqual(len(response.json()['Resources']), 5)


if __name__ == '__main__':
    unittest.main()