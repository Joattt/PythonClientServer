import socket
import sys
import time
import logging
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject
sys.path.append('../')
from common.utils import send_data, get_data
# from common.variables import *
from common.errors import ServerError

client_logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.database = database
        self.username = username
        self.transport = None
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                client_logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            client_logger.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            client_logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
        self.running = True

    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)
        connected = False
        for i in range(5):
            client_logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)
        if not connected:
            client_logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')
        client_logger.debug('Установлено соединение с сервером')
        try:
            with socket_lock:
                send_data(self.create_presence(), self.transport)
                self.process_server_ans(get_data(self.transport))
        except (OSError, json.JSONDecodeError):
            client_logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')
        client_logger.info('Соединение с сервером успешно установлено.')

    def create_presence(self):
        presence = {
            'action': 'presence',
            'time': time.time(),
            'user': {
                'account_name': self.username
            }
        }
        client_logger.debug(f'Сформировано presence-сообщение для пользователя {self.username}')
        return presence

    def process_server_ans(self, message):
        client_logger.debug(f'Разбор сообщения от сервера: {message}')
        if 'response' in message:
            if message['response'] == 200:
                return
            elif message['response'] == 400:
                raise ServerError(f'{message["error"]}')
            else:
                client_logger.debug(f'Принят неизвестный код подтверждения {message["response"]}')
        elif 'action' in message \
                and message['action'] == 'message' \
                and 'sender' in message \
                and 'to' in message \
                and 'message_text' in message \
                and message['to'] == self.username:
            client_logger.debug(f'Получено сообщение от пользователя {message["sender"]}:'
                         f'{message["message_text"]}')
            self.database.save_message(message['sender'], 'in', message['message_text'])
            self.new_message.emit(message['sender'])

    def contacts_list_update(self):
        client_logger.debug(f'Запрос контакт листа для пользователя {self.name}')
        req = {
            'action': 'get_contacts',
            'time': time.time(),
            'user': self.username
        }
        client_logger.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_data(req, self.transport)
            ans = get_data(self.transport)
        client_logger.debug(f'Получен ответ {ans}')
        if 'response' in ans and ans['response'] == 202:
            for contact in ans['list_info']:
                self.database.add_contact(contact)
        else:
            client_logger.error('Не удалось обновить список контактов.')

    def user_list_update(self):
        client_logger.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            'action': 'users_request',
            'time': time.time(),
            'account_name': self.username
        }
        with socket_lock:
            send_data(req, self.transport)
            ans = get_data(self.transport)
        if 'response' in ans and ans['response'] == 202:
            self.database.add_users(ans['list_info'])
        else:
            client_logger.error('Не удалось обновить список известных пользователей.')

    def add_contact(self, contact):
        client_logger.debug(f'Создание контакта {contact}')
        req = {
            'action': 'add_contact',
            'time': time.time(),
            'user': self.username,
            'account_name': contact
        }
        with socket_lock:
            send_data(req, self.transport)
            self.process_server_ans(get_data(self.transport))

    def remove_contact(self, contact):
        client_logger.debug(f'Удаление контакта {contact}')
        req = {
            'action': 'remove_contact',
            'time': time.time(),
            'user': self.username,
            'account_name': contact
        }
        with socket_lock:
            send_data(self.transport, req)
            self.process_server_ans(get_data(self.transport))

    def transport_shutdown(self):
        self.running = False
        message = {
            'action': 'exit',
            'time': time.time(),
            'account_name': self.username
        }
        with socket_lock:
            try:
                send_data(message, self.transport)
            except OSError:
                pass
        client_logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_message(self, to, message):
        message_dict = {
            'action': 'message',
            'sender': self.username,
            'to': to,
            'time': time.time(),
            'message_text': message
        }
        client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        with socket_lock:
            send_data(message_dict, self.transport)
            self.process_server_ans(get_data(self.transport))
            client_logger.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        client_logger.debug('Запущен процесс - приёмник сообщений с сервера.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_data(self.transport)
                except OSError as err:
                    if err.errno:
                        client_logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError, TypeError):
                    client_logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    client_logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
