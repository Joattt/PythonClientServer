import time
import sys
import logging
import argparse
import select
import logs.server_log_config
from common.utils import get_data, send_data
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

server_logger = logging.getLogger('server')


def process_message(message, messages_list, client):
    server_logger.debug(f'Обработка сообщения от клиента: {message}')
    if 'action' in message and message['action'] == 'presence' and 'time' in message and 'user' in message \
            and message['user']['account_name'] == 'Guest':
        server_logger.info(f'Запрос обработан успешно.')
        response = {
            'response': 200,
            'time': time.time(),
            'alert': 'Ok, I see you!'
        }
        send_data(response, client)
        server_logger.info(f'Клиенту отправлен ответ: {response}')
        return
    elif 'action' in message and message['action'] == 'message' and 'time' in message \
            and 'message_text' in message:
        messages_list.append((message['account_name'], message['message_text']))
        return
    else:
        server_logger.warning(f'Получен неверный запрос: {message}')
        response = {
            'response': 400,
            'time': time.time(),
            'alert': 'Bad Request'
        }
        server_logger.warning(f'Клиенту отправлен ответ; {response}')
        return response


def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    args = parser.parse_args(sys.argv[1:])
    listen_addr = args.a
    listen_port = args.p
    if not 1023 < listen_port < 65536:
        server_logger.critical(
            f'При запуске сервера в качестве порта указано не число в диапазоне '
            f'от 1024 до 65535: {listen_port}')
        sys.exit(1)
    return listen_addr, listen_port


def server():
    listen_addr, listen_port = args_parser()
    server_logger.info(
        f'Сервер успешно запущен, порт: {listen_port}; адрес, с которого принимаются подключения: {listen_addr} '
        f'(если адрес не указан, подключения принимаются с любых адресов).')
    server_sock = socket(AF_INET, SOCK_STREAM)
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_sock.bind((listen_addr, listen_port))
    server_sock.settimeout(0.5)
    server_sock.listen(MAX_CONNECTIONS)
    clients_list = []
    messages_list = []
    while True:
        try:
            client_sock, client_addr = server_sock.accept()
        except OSError:
            pass
        else:
            server_logger.info(f'Установлено соединение с клиентом {client_addr}')
            clients_list.append(client_sock)
        senders_list = []
        listeners_list = []
        try:
            if clients_list:
                senders_list, listeners_list, error_list = select.select(clients_list, clients_list, [], 0)
        except OSError:
            pass
        if senders_list:
            for sender in senders_list:
                try:
                    process_message(get_data(sender), messages_list, sender)
                except:
                    server_logger.info(f'Клиент {sender.getpeername()} отключился от сервера.')
                    clients_list.remove(sender)
        if messages_list and listeners_list:
            message = {
                'action': 'message',
                'sender': messages_list[0][0],
                'time': time.time(),
                'message_text': messages_list[0][1]
            }
            del messages_list[0]
            for listener in listeners_list:
                try:
                    send_data(message, listener)
                except:
                    server_logger.info(f'Клиент {listener.getpeername()} отключился от сервера.')
                    listener.close()
                    clients_list.remove(listener)


if __name__ == '__main__':
    server()
