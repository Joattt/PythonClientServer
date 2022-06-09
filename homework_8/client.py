import json
import time
import sys
import logging
import argparse
import threading
import logs.client_log_config
from common.utils import get_data, send_data
from common.variables import DEFAULT_ADDRESS, DEFAULT_PORT
from socket import socket, AF_INET, SOCK_STREAM

client_logger = logging.getLogger('client')


def compose_presence(acc_name):
    presence = {
        'action': 'presence',
        'time': time.time(),
        'type': 'status',
        'user': {
            'account_name': acc_name,
            'status': 'Hi, I am here!'
        }
    }
    client_logger.debug(f'Сформировано presence-сообщение от пользователя {acc_name}: {presence}')
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


def process_message_serv(sock, my_acc_name):
    while True:
        try:
            message = get_data(sock)
            if 'action' in message and message['action'] == 'message' and 'from' in message and \
                    'message_text' in message and 'to' in message and message['to'] == my_acc_name:
                print(f'Получено сообщение от пользователя {message["from"]}:\n{message["message_text"]}')
                client_logger.info(f'Получено сообщение от пользователя {message["from"]}:\n{message["message_text"]}')
            else:
                client_logger.error(f'Получено некорректное сообщение с сервера: {message}')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            client_logger.critical(f'Потеряно соединение с сервером.')
            break


def create_message(client_socket, acc_name='Guest'):
    recipient = input('Введите получателя сообщения: ')
    message = input('Введите сообщение: ')
    message_dict = {
        'action': 'message',
        'from': acc_name,
        'to': recipient,
        'time': time.time(),
        'message_text': message
    }
    client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')
    try:
        send_data(message_dict, client_socket)
        client_logger.info(f'Отправлено сообщение для пользователя {recipient}.')
    except Exception as e:
        print(e)
        client_logger.critical('Потеряно соединение с сервером.')
        sys.exit(1)


def user_commands(sock, acc_name):
    print('Доступные команды: message - ввести сообщение, quit - выйти из чата.')
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            create_message(sock, acc_name)
        elif command == 'quit':
            messasge = {
                'action': 'exit',
                'time': time.time(),
                'account_name': acc_name
            }
            send_data(messasge, sock)
            print('Завершение работы.')
            client_logger.info(f'Пользователь {acc_name} завершил работу.')
            time.sleep(0.5)
            break
        else:
            print('Введена неверная команда.')


def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    args = parser.parse_args(sys.argv[1:])
    server_addr = args.addr
    server_port = args.port
    client_name = args.name
    if not 1023 < server_port < 65536:
        client_logger.critical(
            f'При запуске клиента в качестве порта указано не число в диапазоне '
            f'от 1024 до 65535: {server_port}')
        sys.exit(1)
    return server_addr, server_port, client_name


def client():
    server_addr, server_port, client_name = args_parser()
    print(f'Клиентский модуль, имя пользователя {client_name}')
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    client_logger.info(f'Запущен клиент, сервер: {server_addr}, порт: {server_port}, пользователь: {client_name}.')
    try:
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((server_addr, server_port))
        send_data(compose_presence(client_name), client_sock)
        client_logger.info(f'Presence-сообщение отправлено на сервер {server_addr}.')
        response = parse_response(get_data(client_sock))
        client_logger.info(f'Статус ответа с сервера: {response}')
        print(f'Установлено соединение с сервером.')
        client_logger.info(f'Клиент {client_name} установил соединение с сервером.')
    except (ValueError, json.JSONDecodeError):
        client_logger.error(f'Не удалось декодировать ответ сервера.')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        client_logger.critical(f'Не удалось подключиться к серверу {server_addr}:{server_port}')
        sys.exit(1)
    else:
        recipient = threading.Thread(target=process_message_serv, args=(client_sock, client_name))
        recipient.daemon = True
        recipient.start()
        sender = threading.Thread(target=user_commands, args=(client_sock, client_name))
        sender.daemon = True
        sender.start()
        client_logger.debug('Запущены процессы приема и отправки сообщений.')
        while True:
            time.sleep(1)
            if recipient.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    client()
