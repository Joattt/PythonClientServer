import json
import time
import sys
import logging
import logs.client_log_config
from common.utils import get_data, send_data
from common.variables import DEFAULT_ADDRESS, DEFAULT_PORT
from socket import socket, AF_INET, SOCK_STREAM

client_logger = logging.getLogger('client')


def compose_presence(account_name='Guest'):
    presence = {
        'action': 'presence',
        'time': time.time(),
        'type': 'status',
        'user': {
            'account_name': account_name,
            'status': 'Hi, I am here!'
        }
    }
    client_logger.debug(f'Сформировано presence-сообщение от пользователя {account_name}: {presence}')
    return presence


def parse_response(response):
    client_logger.debug(f'Разбор ответа от сервера: {response}')
    if 'response' in response:
        if response['response'] == 200:
            return '200'
        client_logger.warning(f'Статус ответа {response["response"]}')
        return '400'
    client_logger.error(f'Получен неверный ответ от сервера: {response}')
    raise ValueError


def client():
    try:
        addr = DEFAULT_ADDRESS if len(sys.argv) <= 1 else sys.argv[1]
        port = DEFAULT_PORT if len(sys.argv) <= 2 else int(sys.argv[2])
        if port < 1024 or port > 65535:
            raise ValueError
    except ValueError:
        client_logger.error(f'В качестве порта указано не число в диапазоне от 1024 до 65535: {port}')
    client_sock = socket(AF_INET, SOCK_STREAM)
    client_sock.connect((addr, port))
    client_logger.info(f'Установено соединение с сервером, адрес: {addr}, порт: {port}')
    send_data(compose_presence(), client_sock)
    client_logger.info(f'Presence-сообщение отправлено на сервер {addr}.')
    try:
        response = parse_response(get_data(client_sock))
        client_logger.info(f'Статус ответа с сервера: {response}')
        client_sock.close()
    except (ValueError, json.JSONDecodeError):
        client_logger.error(f'Не удалось декодировать ответ сервера.')
        client_sock.close()


if __name__ == '__main__':
    client()
