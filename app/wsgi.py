from main import application, socketio
import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='"%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"',
                    datefmt='%m/%d/%Y %I:%M:%S %p', stream=sys.stdout)

if __name__ == "__main__":
    logging.info("Server attempting to start")
    socketio.run(application)

