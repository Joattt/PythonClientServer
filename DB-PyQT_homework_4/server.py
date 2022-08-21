import time
import sys
import os
import logging
import argparse
import select
import socket
import threading
import configparser
import logs.server_log_config
from common.utils import get_data, send_data
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, RESPONSE_200, RESPONSE_400, RESPONSE_202
from metaclasses import ServerMaker
from descriptors import Port
from server_database import ServerStorage
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

server_logger = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()


def args_parser(default_port, default_addr):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_addr, nargs='?')
    args = parser.parse_args(sys.argv[1:])
    listen_addr = args.a
    listen_port = args.p
    return listen_addr, listen_port


class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_addr, listen_port, database):
        self.addr = listen_addr
        self.port = listen_port
        self.database = database
        self.clients = []
        self.messages = []
        self.names = dict()
        super().__init__()

    def process_message_dest(self, message, listen_socks):
        if message['to'] in self.names and self.names[message['to']] in listen_socks:
            send_data(message, self.names[message['to']])
            server_logger.info(f'Отправлено сообщение пользователю {message["to"]} от пользователя {message["from"]}.')
        elif message['to'] in self.names and self.names[message['to']] not in listen_socks:
            raise ConnectionError
        else:
            server_logger.error(f'Пользователь {message["to"]} не зарегистрирован, сообщение не отправлено.')

    def process_message_cl(self, message, client):
        global new_connection
        server_logger.debug(f'Обработка сообщения от клиента: {message}')
        if 'action' in message and message['action'] == 'presence' and 'time' in message and 'user' in message:
            if message['user']['account_name'] not in self.names.keys():
                self.names[message['user']['account_name']] = client
                client_addr, client_port = client.getpeername()
                self.database.user_login(message['user']['account_name'], client_addr, client_port)
                server_logger.info(f'Запрос обработан успешно.')
                response = RESPONSE_200
                send_data(response, client)
                server_logger.info(f'Клиенту отправлен ответ: {response}')
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                send_data(response, client)
                self.clients.remove(client)
                client.close()
            return
        elif 'action' in message and message['action'] == 'message' and 'time' in message \
                and 'message_text' in message and 'to' in message and 'from' in message \
                and self.names[message['from']] == client:
            self.messages.append(message)
            self.database.process_message_dest(message['from'], message['to'])
            return
        elif 'action' in message and message['action'] == 'exit' and 'account_name' in message \
                and self.names[message['account_name']] == client:
            self.database.user_logout(message['account_name'])
            server_logger.info(f'Клиент {message["account_name"]} корректно отключился от сервера.')
            self.clients.remove(self.names[message['account_name']])
            self.names[message['account_name']].close()
            del self.names[message['account_name']]
            with conflag_lock:
                new_connection = True
            return
        elif 'action' in message and message['action'] == 'get_contacts' and 'user' in message \
                and self.names[message['user']] == client:
            response = RESPONSE_202
            response['list_info'] = self.database.get_contacts(message['user'])
            send_data(response, client)
        elif 'action' in message and message['action'] == 'add_contact' and 'account_name' in message \
               and 'user' in message and self.names[message['user']] == client:
            self.database.add_contact(message['user'], message['account_name'])
            send_data(RESPONSE_200, client)
        elif 'action' in message and message['action'] == 'remove_contact' and 'account_name' in message \
               and 'user' in message and self.names[message['user']] == client:
            self.database.remove_contact(message['user'], message['account_name'])
            send_data(RESPONSE_200, client)
        elif 'action' in message and message['action'] == 'users_request' and 'account_name' in message \
               and self.names[message['account_name']] == client:
            response = RESPONSE_202
            response['list_info'] = [user[0] for user in self.database.users_list()]
            send_data(response, client)
        else:
            server_logger.warning(f'Получен неверный запрос: {message}')
            response = RESPONSE_400
            send_data(response, client)
            server_logger.warning(f'Клиенту отправлен ответ: {response}')
            return

    def start_socket(self):
        server_logger.info(
            f'Сервер успешно запущен, порт: {self.port}; адрес, с которого принимаются подключения: {self.addr} '
            f'(если адрес не указан, подключения принимаются с любых адресов).')
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.addr, self.port))
        server_sock.settimeout(0.5)
        self.sock = server_sock
        self.sock.listen()

    def run(self):
        self.start_socket()

        while True:
            try:
                client_sock, client_addr = self.sock.accept()
            except OSError:
                pass
            else:
                server_logger.info(f'Установлено соединение с клиентом {client_addr}')
                self.clients.append(client_sock)

            senders_list = []
            listeners_list = []
            try:
                if self.clients:
                    senders_list, listeners_list, error_list = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass
            if senders_list:
                for sender in senders_list:
                    try:
                        self.process_message_cl(get_data(sender), sender)
                    except OSError:
                        server_logger.info(f'Клиент {sender.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == sender:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(sender)
            for message in self.messages:
                try:
                    self.process_message_dest(message, listeners_list)
                except:
                    server_logger.info(f'Связь с клиентом {message["to"]} потеряна.')
                    self.clients.remove(self.names[message['to']])
                    self.database.user_logout(message['to'])
                    del self.names[message['to']]
            self.messages.clear()


def main():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_addr, listen_port = args_parser(config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    server = Server(listen_addr, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
