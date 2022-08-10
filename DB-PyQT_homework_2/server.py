import time
import sys
import logging
import argparse
import select
import socket
import logs.server_log_config
from common.utils import get_data, send_data
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS
from metaclasses import ServerMaker
from descriptors import Port

server_logger = logging.getLogger('server')


def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    args = parser.parse_args(sys.argv[1:])
    listen_addr = args.a
    listen_port = args.p
    return listen_addr, listen_port


class Server(metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_addr, listen_port):
        self.addr = listen_addr
        self.port = listen_port
        self.clients = []
        self.messages = []
        self.names = dict()

    def process_message_dest(self, message, listen_socks):
        if message['to'] in self.names and self.names[message['to']] in listen_socks:
            send_data(message, self.names[message['to']])
            server_logger.info(f'Отправлено сообщение пользователю {message["to"]} от пользователя {message["from"]}.')
        elif message['to'] in self.names and self.names[message['to']] not in listen_socks:
            raise ConnectionError
        else:
            server_logger.error(f'Пользователь {message["to"]} не зарегистрирован, сообщение не отправлено.')

    def process_message_cl(self, message, client):
        server_logger.debug(f'Обработка сообщения от клиента: {message}')
        if 'action' in message and message['action'] == 'presence' and 'time' in message and 'user' in message:
            if message['user']['account_name'] not in self.names.keys():
                self.names[message['user']['account_name']] = client
                server_logger.info(f'Запрос обработан успешно.')
                response = {
                    'response': 200,
                    'time': time.time(),
                    'alert': 'Ok, I see you!'
                }
                send_data(response, client)
                server_logger.info(f'Клиенту отправлен ответ: {response}')
            else:
                response = {
                    'response': 400,
                    'time': time.time(),
                    'alert': 'Username is already taken'
                }
                send_data(response, client)
                self.clients.remove(client)
                client.close()
            return
        elif 'action' in message and message['action'] == 'message' and 'time' in message \
                and 'message_text' in message and 'to' in message and 'from' in message:
            self.messages.append(message)
            return
        elif 'action' in message and message['action'] == 'exit' and 'account_name' in message:
            self.clients.remove(self.names[message['account_name']])
            self.names[message['account_name']].close()
            del self.names[message['account_name']]
            # self.clients.remove(self.names['account_name'])
            # self.names['account_name'].close()
            # del self.names['account_name']
            return
        else:
            server_logger.warning(f'Получен неверный запрос: {message}')
            response = {
                'response': 400,
                'time': time.time(),
                'alert': 'Bad request'
            }
            send_data(response, client)
            server_logger.warning(f'Клиенту отправлен ответ: {response}')
            return

    def start_socket(self):
        server_logger.info(
            f'Сервер успешно запущен, порт: {self.port}; адрес, с которого принимаются подключения: {self.addr} '
            f'(если адрес не указан, подключения принимаются с любых адресов).')
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.addr, self.port))
        server_sock.settimeout(0.5)
        self.sock = server_sock
        self.sock.listen()

    def main_cycle(self):
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
                    except:
                        server_logger.info(f'Клиент {sender.getpeername()} отключился от сервера.')
                        self.clients.remove(sender)
            for message in self.messages:
                try:
                    self.process_message_dest(message, listeners_list)
                except:
                    server_logger.info(f'Связь с клиентом {message["to"]} потеряна.')
                    self.clients.remove(self.names[message['to']])
                    del self.names[message['to']]
            self.messages.clear()


def main():
    listen_addr, listen_port = args_parser()
    server = Server(listen_addr, listen_port)
    server.main_cycle()


if __name__ == '__main__':
    main()
