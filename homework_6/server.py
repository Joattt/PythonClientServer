import json
import time
import sys
import logging
import logs.server_log_config
from common.utils import get_data, send_data
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

server_logger = logging.getLogger('server')


def compose_confirmation(message):
    server_logger.debug(f'Обработка сообщения от клиента: {message}')
    if 'action' in message and message['action'] == 'presence' and 'time' in message and 'user' in message \
            and message['user']['account_name'] == 'Guest':
        server_logger.info(f'Запрос обработан успешно.')
        response = {
            'response': 200,
            'time': time.time(),
            'alert': 'Ok, I see you!'
        }
        server_logger.info(f'Клиенту отправлен ответ: {response}')
        return response
    server_logger.warning(f'Получен неверный запрос: {message}')
    response = {
        'response': 400,
        'time': time.time(),
        'alert': 'Bad Request'
    }
    server_logger.warning(f'Клиенту отправлен ответ; {response}')
    return response


def server():
    try:
        port = DEFAULT_PORT if '-p' not in sys.argv else int(sys.argv[sys.argv.index('-p') + 1])
        if port < 1024 or port > 65535:
            raise ValueError
    except IndexError:
        server_logger.error(f"После параметра '-p' не указан порт.")
    except ValueError:
        server_logger.error(f'При запуске сервера в качестве порта указано не число в диапазоне '
                            f'от 1024 до 65535: {port}')
    try:
        addr = '' if '-a' not in sys.argv else sys.argv[sys.argv.index('-a') + 1]
    except IndexError:
        server_logger.error(f"После параметра '-a' не указан адрес.")
    server_logger.info(f'Сервер успешно запущен, порт: {port}; адрес, с которого принимаются подключения: {addr} '
                       f'(если адрес не указан, подключения принимаются с любых адресов).')
    server_sock = socket(AF_INET, SOCK_STREAM)
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_sock.bind((addr, port))
    server_sock.listen(MAX_CONNECTIONS)
    while True:
        client_sock, addr = server_sock.accept()
        server_logger.info(f'Установлено соедение с клиентом {addr}')
        try:
            message_received = get_data(client_sock)
            server_logger.info(f'От клиента {addr} получено сообщение {message_received}')
            send_data(compose_confirmation(message_received), client_sock)
            client_sock.close()
        except (ValueError, json.JSONDecodeError):
            server_logger.error(f'Не удалось декодировать сообщение от клиента.')
            client_sock.close()


if __name__ == '__main__':
    server()
