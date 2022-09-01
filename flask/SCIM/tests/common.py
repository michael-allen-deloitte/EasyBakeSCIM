from os import path, listdir, remove
from sys import exit
from json import load
from logging import Logger
from requests import Response, get, post, put
from configparser import ConfigParser
from urllib.parse import urljoin

config = ConfigParser()
config_path = './tests.ini'
if path.exists(config_path):
    config.read(config_path)
else:
    print('Could not read config file from path %s' % config_path)
    exit(1)

BASE_URL: str = config['Deployment']['base_url']
GET_ID: str = config['Deployment']['get_id']
CACHE_DIR: str = config['Cache']['dir'].strip('/').strip('\\')
LOCAL_DEPLOYMENT: bool = config['Deployment']['local'].lower() == 'true'

class TestHelper:
    def __init__(self, endpoint_uri: str, logger: Logger) -> None:
        self.endpoint_uri = endpoint_uri
        self.logger = logger

    def clear_cache(self) -> bool:
        if LOCAL_DEPLOYMENT:
            if path.exists(CACHE_DIR):
                cache_files = listdir(CACHE_DIR)
                cache_files.remove('empty')
                if len(cache_files) > 0:
                    self.logger.info('Cleaning up any existing local cache')
                    for file in cache_files:
                        remove(path.join(CACHE_DIR, file))
        else:
            self.logger.info('Clearing existing remote cache')
            request_url = BASE_URL.strip('/') + '/ClearCache'
            response = get(request_url, verify=False)
            return response.status_code == 204
        return True

    def post_file_contents(self, file_path: str) -> Response:
        with open(file_path, 'r') as data_file:
            test_data = load(data_file)
        request_url = urljoin(BASE_URL.strip('/'), self.endpoint_uri.strip('/'))
        self.logger.info('Making POST to %s' % request_url)
        return post(request_url, json=test_data, verify=False)

    def put_file_contents(self, file_path: str, resource_key: str = 'id') -> Response:
        with open(file_path, 'r') as data_file:
            test_data = load(data_file)
        request_url = urljoin(BASE_URL.strip('/'), self.endpoint_uri.strip('/'), test_data[resource_key])
        self.logger.info('Making PUT to %s' % request_url)
        return put(request_url, json=test_data, verify=False)