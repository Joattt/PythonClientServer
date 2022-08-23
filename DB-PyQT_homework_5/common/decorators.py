from functools import wraps
import logging
import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..'))
import logs.client_log_config
import logs.server_log_config


def log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        function_module = func.__module__
        function_caller = sys._getframe().f_back.f_code.co_name
        logger = logging.getLogger('client') if 'client_send.py' in sys.argv[0] else logging.getLogger('server')
        logger.debug(f'Вызов функции {function_name} из модуля {function_module} с параметрами: {args}, {kwargs}'
                     f'Вызов из функции {function_caller}')
        result = func(*args, **kwargs)
        logger.debug(f'Функция {function_name} успешно завершена. Результат: {result}')
        return result
    return wrapper
