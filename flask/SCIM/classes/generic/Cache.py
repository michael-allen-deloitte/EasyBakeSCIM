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
            # if there is no cache lock overwrite it
            # if there is a lock file do nothing
            if not self.check_for_lock_file():
                logger.info('Cache no longer valid and no lock in place, refreshing cache')
                os.remove(self.cache_file_path)
                cache_file = open(self.cache_file_path, 'w')
                json.dump(json_obj, cache_file)
                cache_file.close()
        # if not write it
        else:
            logger.info('No cache found, writing data to cache')
            with open(self.cache_file_path, 'w') as cache_file:
                json.dump(json_obj, cache_file)
        
    def read_json_cache(self) -> Union[List[dict], dict]:
        if self.check_cache_lifetime_valid():
            logger.info('Reading data from cache')
            with open(self.cache_file_path, 'r') as cache_file:
                return json.load(cache_file)
        elif not self.check_cache_lifetime_valid() and self.check_for_lock_file():
            logger.info('Cache has timed out but is currently locked, reading from expired cache')
            with open(self.cache_file_path, 'r') as cache_file:
                return json.load(cache_file)
        else:
            logger.info('Cache has timed out and no lock file exists')
            raise TimeoutError('The cache has timed out')

    # create a lock file and add a 'start' to the beginning to notate a pagination process is using it
    def create_lock_file(self, identifier_string: str = '') -> None:
        lock_file = open(self.cache_file_path + '.lock', 'w')
        lock_file.write('start\t' + identifier_string)
        lock_file.close()

    # if a second pagination process needs access to the cache so data is not overwritten
    # append a 'start' to the lock file to notate another pagination process is using it
    # when a pagination loop is completed, append 'end' to the lock file
    # lock files can only be removed when the number of 'starts' equals the number of 'ends'
    # this way the cache will not be modified in the middle of a pagination process
    def append_lock_file(self, text: str) -> None:
        lock_file = open(self.cache_file_path + '.lock', 'a')
        lock_file.write('\n' + text)
        lock_file.close()

    # lock files can only be removed when the number of 'starts' equals the number of 'ends'
    # this way the cache will not be modified in the middle of a pagination process
    def cleanup_lock_file(self, force = False) -> None:
        if force:
            logger.info('Force deleting lock file')
            if os.path.exists(self.cache_file_path + '.lock'): os.remove(self.cache_file_path + '.lock')
        else:
            with open(self.cache_file_path + '.lock', 'r') as lock_file:
                file_contents = lock_file.read()
            if file_contents.count('start') == file_contents.count('end'):
                logger.info('All threads finished with lock file, deleting it')
                os.remove(self.cache_file_path + '.lock')
            else:
                logger.info('There is a thread still using the cache lock, once that thread is completed the lock will be removed')

    def check_for_lock_file(self) -> bool:
        return os.path.isfile(self.cache_file_path + '.lock')