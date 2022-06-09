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


def process_message_cl(message, messages_list, client, clients_list, acc_names):
    server_logger.debug(f'Обработка сообщения от клиента: {message}')
    if 'action' in message and message['action'] == 'presence' and 'time' in message and 'user' in message:
        if message['user']['account_name'] not in acc_names.keys():
            acc_names[message['user']['account_name']] = client
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
            clients_list.remove(client)
            client.close()
        return
    elif 'action' in message and message['action'] == 'message' and 'time' in message \
            and 'message_text' in message and 'to' in message and 'from' in message:
        messages_list.append(message)
        return
    elif 'action' in message and message['action'] == 'exit' and 'account_name' in message:
        clients_list.remove(acc_names[message['account_name']])
        acc_names[message['account_name']].close()
        del acc_names[message['account_name']]
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


def process_message_dest(message, acc_names, listen_socks):
    if message['to'] in acc_names and acc_names[message['to']] in listen_socks:
        send_data(message, acc_names[message['to']])
        server_logger.info(f'Отправлено сообщение пользователю {message["to"]} от пользователя {message["from"]}.')
    elif message['to'] in acc_names and acc_names[message['to']] not in listen_socks:
        raise ConnectionError
    else:
        server_logger.error(f'Пользователь {message["to"]} не зарегистрирован, сообщение не отправлено.')


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
    acc_names = dict()
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
                    process_message_cl(get_data(sender), messages_list, sender, clients_list, acc_names)
                except Exception:
                    server_logger.info(f'Клиент {sender.getpeername()} отключился от сервера.')
                    clients_list.remove(sender)
        for message in messages_list:
            try:
                process_message_dest(message, acc_names, listeners_list)
            except Exception:
                server_logger.info(f'Связь с клиентом {message["to"]} потеряна.')
                clients_list.remove(acc_names[message['to']])
                del acc_names[message['to']]
        messages_list.clear()


if __name__ == '__main__':
    server()
