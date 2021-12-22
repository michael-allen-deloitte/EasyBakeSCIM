import logging, sys, os
from pathlib import Path

from SCIM import app, LOG_LEVEL, LOG_FORMAT, LOCAL_DATABASE
from SCIM.examples.populate_example_db import generate_example_database

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LOG_FORMAT)
logger.addHandler(stream_handler)

if __name__ == '__main__':
    cmd_args = sys.argv
    if LOCAL_DATABASE:
        db_file = Path('./SCIM/example.db')
        if not db_file.is_file():
            logger.info('No example database found, creating and populating')
            generate_example_database('./SCIM/examples/users.csv')
        elif '--flush' in cmd_args:
            if os.path.exists('./SCIM/example.db'):
                logger.info('Deleting old example database')
                os.remove('./SCIM/example.db')
            logger.info('Populating example database')
            generate_example_database('./SCIM/examples/users.csv')
    
    app.run(host='0.0.0.0', port=5001)