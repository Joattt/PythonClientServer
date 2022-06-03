import logging
import os
import sys
sys.path.append('../')

client_logger = logging.getLogger('client')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client.log')
file_handler = logging.FileHandler(log_path, encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
client_logger.addHandler(file_handler)
client_logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    client_logger.debug('debug')
    client_logger.info('info')
    client_logger.warning('warning')
    client_logger.error('error')
    client_logger.critical('critical')
