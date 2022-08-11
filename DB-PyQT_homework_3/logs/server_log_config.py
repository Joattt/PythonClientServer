import logging
import logging.handlers
import os
import sys
sys.path.append('../')

server_logger = logging.getLogger('server')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log')
rot_handler = logging.handlers.TimedRotatingFileHandler(log_path, when='midnight', encoding='utf-8')
rot_handler.setFormatter(formatter)
rot_handler.setLevel(logging.DEBUG)
server_logger.addHandler(rot_handler)
server_logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    server_logger.debug('debug')
    server_logger.info('info')
    server_logger.warning('warning')
    server_logger.error('error')
    server_logger.critical('critical')
