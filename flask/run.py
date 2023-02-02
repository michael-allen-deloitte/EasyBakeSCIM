import sys, os
from pathlib import Path

from SCIM import app, LOCAL_DATABASE, config
from SCIM.helpers import set_up_logger
from SCIM.examples.populate_example_db import generate_example_database

logger = set_up_logger(__name__)

if __name__ == '__main__':
    cmd_args = sys.argv
    if LOCAL_DATABASE:
        db_file = Path('./SCIM/example.db')
        if not db_file.is_file():
            logger.info('No example database found, creating and populating')
            generate_example_database('./SCIM/examples/users.csv', './SCIM/examples/groups-no-members.csv', './SCIM/examples/group-membership.csv')
        elif '--flush' in cmd_args:
            if os.path.exists('./SCIM/example.db'):
                logger.info('Deleting old example database')
                os.remove('./SCIM/example.db')
            logger.info('Populating example database')
            generate_example_database('./SCIM/examples/users.csv', './SCIM/examples/groups-no-members.csv', './SCIM/examples/group-membership.csv')
            cache_dir = config['Cache']['dir']
            if os.path.exists(cache_dir):
                cache_files = os.listdir(cache_dir)
                cache_files.remove('empty')
                if len(cache_files) > 0:
                    logger.info('Cleaning up any existing cache')
                    for file in cache_files:
                        os.remove(os.path.join(cache_dir, file))
    
    app.run(host='127.0.0.1', port=5001)