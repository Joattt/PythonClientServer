import json
import time
import sys
import logging
import argparse
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


def process_message(message):
    if 'action' in message and message['action'] == 'message' and 'sender' in message and \
            'message_text' in message:
        print(f'Получено сообщение от пользователя {message["sender"]}:\n{message["message_text"]}')
        client_logger.info(f'Получено сообщение от пользователя {message["sender"]}:\n{message["message_text"]}')
    else:
        client_logger.error(f'Получено некорректное сообщение с сервера: {message}')


def create_message(client_socket, account_name='Guest'):
    message = input('Введите сообщение или "quit" для выхода из чата: ')
    if message == 'quit':
        client_socket.close()
        print('Пользователь завершил работу.')
        client_logger.info('Пользователь завершил работу.')
        sys.exit(0)
    message_dict = {
        'action': 'message',
        'time': time.time(),
        'account_name': account_name,
        'message_text': message
    }
    client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')
    return message_dict


def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('addr', default=DEFAULT_ADDRESS, nargs='?')
    parser.add_argument('-m', '--mode', default='send', nargs='?')
    args = parser.parse_args(sys.argv[1:])
    server_addr = args.addr
    server_port = args.port
    client_mode = args.mode
    if not 1023 < server_port < 65536:
        client_logger.critical(
            f'При запуске клиента в качестве порта указано не число в диапазоне '
            f'от 1024 до 65535: {server_port}')
        sys.exit(1)
    if client_mode not in ('listen', 'send'):
        client_logger.critical(f'Указан неверный режим работы: {client_mode}.')
        sys.exit(1)
    return server_addr, server_port, client_mode


def client():
    server_addr, server_port, client_mode = args_parser()
    client_logger.info(f'Запущен клиент, адрес сервера: {server_addr}, порт: {server_port}, режим: {client_mode}.')
    try:
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((server_addr, server_port))
        send_data(compose_presence(), client_sock)
        client_logger.info(f'Presence-сообщение отправлено на сервер {server_addr}.')
        response = parse_response(get_data(client_sock))
        client_logger.info(f'Статус ответа с сервера: {response}')
        print(f'Установлено соединение с сервером.')
        client_logger.info(f'Установлено соединение с сервером.')
    except (ValueError, json.JSONDecodeError):
        client_logger.error(f'Не удалось декодировать ответ сервера.')
        sys.exit(1)
    else:
        if client_mode == 'send':
            print('Режим отправки сообщений.')
        else:
            print('Режим приема сообщений.')
        while True:
            if client_mode == 'send':
                send_data(create_message(client_sock), client_sock)
            if client_mode == 'listen':
                process_message(get_data(client_sock))


if __name__ == '__main__':
    client()
