import json
import time
import sys
import logging
import argparse
import threading
import socket
import logs.client_log_config
from common.utils import get_data, send_data
from common.variables import DEFAULT_ADDRESS, DEFAULT_PORT
from metaclasses import ClientMaker

client_logger = logging.getLogger('client')


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, acc_name, sock):
        self.acc_name = acc_name
        self.sock = sock
        super().__init__()

    def create_message(self):
        recipient = input('Введите получателя сообщения: ')
        message = input('Введите сообщение: ')
        message_dict = {
            'action': 'message',
            'from': self.acc_name,
            'to': recipient,
            'time': time.time(),
            'message_text': message
        }
        client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_data(message_dict, self.sock)
            client_logger.info(f'Отправлено сообщение для пользователя {recipient}.')
        except:
            client_logger.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    def run(self):
        print('Доступные команды: message - ввести сообщение, quit - выйти из чата.')
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'quit':
                try:
                    exit_messasge = {
                        'action': 'exit',
                        'time': time.time(),
                        'account_name': self.acc_name
                    }
                    send_data(exit_messasge, self.sock)
                except:
                    pass
                print('Завершение работы.')
                client_logger.info(f'Пользователь {self.acc_name} завершил работу.')
                time.sleep(0.5)
                break
            else:
                print('Введена неверная команда.')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, acc_name, sock):
        self.acc_name = acc_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_data(self.sock)
                if 'action' in message and message['action'] == 'message' and 'from' in message and \
                        'message_text' in message and 'to' in message and message['to'] == self.acc_name:
                    print(f'Получено сообщение от пользователя {message["from"]}:\n{message["message_text"]}')
                    client_logger.info(
                        f'Получено сообщение от пользователя {message["from"]}:\n{message["message_text"]}')
                else:
                    client_logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                client_logger.critical(f'Потеряно соединение с сервером.')
                break


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


def main():
    server_addr, server_port, client_name = args_parser()
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Запущен клиент с именем {client_name}')
    client_logger.info(f'Запущен клиент, сервер: {server_addr}, порт: {server_port}, пользователь: {client_name}.')
    try:
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        recipient = ClientReader(client_name, client_sock)
        recipient.daemon = True
        recipient.start()
        sender = ClientSender(client_name, client_sock)
        sender.daemon = True
        sender.start()
        client_logger.debug('Запущены процессы приема и отправки сообщений.')
        while True:
            time.sleep(1)
            if recipient.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
