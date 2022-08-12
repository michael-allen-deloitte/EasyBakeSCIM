import os
import json
import platform
import time
import logging
from typing import Union, List

from SCIM import config, LOG_LEVEL, LOG_FORMAT

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

def creation_time(path_to_file) -> float:
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

class Cache:
    cache_base_dir = config['Cache']['dir']
    cache_lifetime_sec = int(config['Cache']['lifetime'])*60

    def __init__(self, file_name: str) -> None:
        if not os.path.exists(self.cache_base_dir):
            os.mkdir(self.cache_base_dir)
        self.cache_file_path = self.cache_base_dir.strip('/').strip('\\') + '/' + file_name
        # if there already exists a cache file on startup delete it
        if os.path.isfile(self.cache_file_path):
            logging.debug('Deleting existing cache')
            os.remove(self.cache_file_path)

    def check_cache_lifetime_valid(self) -> bool:
        cache_created = creation_time(self.cache_file_path)
        return time.time() < cache_created + self.cache_lifetime_sec

    def write_json_cache(self, json_obj: dict) -> None:
        # if the cache already exists
        if os.path.isfile(self.cache_file_path):
            # if its no longer valid overwrite it
            # if it is valid do nothing
            if not self.check_cache_lifetime_valid():
                logger.debug('Cache no longer valid, replacing it')
                os.remove(self.cache_file_path)
                cache_file = open(self.cache_file_path, 'w')
                json.dump(json_obj, cache_file)
                cache_file.close()
        # if not write it
        else:
            logger.debug('No cache found, writing data to cache')
            with open(self.cache_file_path, 'w') as cache_file:
                json.dump(json_obj, cache_file)
        
    
    def read_json_cache(self) -> Union[List[dict], dict]:
        if self.check_cache_lifetime_valid():
            logger.debug('Reading data from cache')
            with open(self.cache_file_path, 'r') as cache_file:
                return json.load(cache_file)
        else:
            logger.debug('Cache has timed out')
            raise TimeoutError('The cache has timed out')