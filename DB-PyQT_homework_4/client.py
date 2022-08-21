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
from client_database import ClientDatabase

client_logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        return {
            'action': 'exit',
            'time': time.time(),
            'account_name': self.account_name
        }

    def create_message(self):
        recipient = input('Введите получателя сообщения: ')
        message = input('Введите сообщение: ')
        with database_lock:
            if not self.database.check_user(recipient):
                client_logger.error(f'Попытка отправить сообщение '
                             f'незарегистрированому получателю: {recipient}')
                return
        message_dict = {
            'action': 'message',
            'from': self.account_name,
            'to': recipient,
            'time': time.time(),
            'message_text': message
        }
        client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        with database_lock:
            self.database.save_message(self.account_name, recipient, message)
        with sock_lock:
            try:
                send_data(message_dict, self.sock)
                client_logger.info(f'Отправлено сообщение для пользователя {recipient}.')
            except:
                client_logger.critical('Потеряно соединение с сервером.')
                sys.exit(1)

    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'quit':
                with sock_lock:
                    try:
                        send_data(self.create_exit_message(), self.sock)
                    except Exception as e:
                        print(e)
                        pass
                    print('Завершение соединения.')
                    client_logger.info(f'Пользователь {self.account_name} завершил работу.')
                    time.sleep(0.5)
                    break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print('Введена неверная команда.')

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - нажать Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    client_logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except Exception:
                        client_logger.error('Не удалось отправить информацию на сервер.')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_data(self.sock)
                except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    client_logger.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if 'action' in message and message['action'] == 'message' and 'from' in message and \
                            'message_text' in message and 'to' in message and message['to'] == self.account_name:
                        print(f'Получено сообщение от пользователя {message["from"]}:\n{message["message_text"]}')
                        with database_lock:
                            try:
                                self.database.save_message(message['from'], self.account_name, message['message_text'])
                            except Exception as e:
                                print(e)
                                client_logger.error('Ошибка взаимодействия с базой данных')
                        client_logger.info(
                            f'Получено сообщение от пользователя {message["from"]}:\n{message["message_text"]}')
                    else:
                        client_logger.error(f'Получено некорректное сообщение с сервера: {message}')


def compose_presence(account_name):
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


def contacts_list_request(sock, name):
    client_logger.debug(f'Запрос контакт листа для пользователя {name}')
    req = {
        'action': 'get_contacts',
        'time': time.time(),
        'user': name
    }
    client_logger.debug(f'Сформирован запрос {req}')
    send_data(req, sock)
    ans = get_data(sock)
    client_logger.debug(f'Получен ответ {ans}')
    if 'response' in ans and ans['response'] == 202:
        return ans['list_info']
    else:
        raise Exception


def add_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {
        'action': 'add_contact',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_data(req, sock)
    ans = get_data(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise Exception
    print('Контакт успешно создан.')


def user_list_request(sock, username):
    client_logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        'actions': 'users_request',
        'time': time.time(),
        'account_name': username
    }
    send_data(req, sock)
    ans = get_data(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['list_info']
    else:
        raise Exception


def remove_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {
        'action': 'remove_contact',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_data(req, sock)
    ans = get_data(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise Exception
    print('Контакт успешно удален.')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except Exception:
        client_logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)
    try:
        contacts_list = contacts_list_request(sock, username)
    except Exception:
        client_logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    print('Консольный мессенджер, клиентский модуль.')
    server_addr, server_port, client_name = args_parser()
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Запущен клиент с именем {client_name}')
    client_logger.info(f'Запущен клиент, сервер: {server_addr}, порт: {server_port}, пользователь: {client_name}.')
    try:
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.settimeout(1)
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
        database = ClientDatabase(client_name)
        database_load(client_sock, database, client_name)
        sender = ClientSender(client_name, client_sock, database)
        sender.daemon = True
        sender.start()
        recipient = ClientReader(client_name, client_sock, database)
        recipient.daemon = True
        recipient.start()
        client_logger.debug('Запущены процессы приема и отправки сообщений.')
        while True:
            time.sleep(1)
            if recipient.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
