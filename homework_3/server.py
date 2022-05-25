from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import json
import time
import sys
from common.utils import get_data, send_data
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS


def compose_confirmation(message):
    if 'action' in message and message['action'] == 'presence' and 'time' in message and 'user' in message \
            and message['user']['account_name'] == 'Guest':
        return {
            'response': 200,
            'time': time.time(),
            'alert': 'Ok, I see you!'
        }
    return {
        'response': 400,
        'time': time.time(),
        'alert': 'Bad Request'
    }


def server():
    try:
        port = DEFAULT_PORT if '-p' not in sys.argv else int(sys.argv[sys.argv.index('-p') + 1])
        if port < 1024 or port > 65535:
            raise ValueError
    except IndexError:
        print("После параметра '-p' нужно указать порт.")
    except ValueError:
        print('Портом может быть только число в диапазоне от 1024 до 65535.')
    try:
        addr = '' if '-a' not in sys.argv else sys.argv[sys.argv.index('-a') + 1]
    except IndexError:
        print("После параметра '-a' нужно указать адрес.")
    server_sock = socket(AF_INET, SOCK_STREAM)
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_sock.bind((addr, port))
    server_sock.listen(MAX_CONNECTIONS)
    while True:
        client_sock, addr = server_sock.accept()
        try:
            message_received = get_data(client_sock)
            print(f'От клиента {addr} получено сообщение {message_received}')
            send_data(compose_confirmation(message_received), client_sock)
            print(f'Клиенту {addr} отправлен ответ: {compose_confirmation(message_received)}')
            client_sock.close()
        except (ValueError, json.JSONDecodeError):
            print('Не удалось декодировать сообщение от клиента.')
            client_sock.close()


if __name__ == '__main__':
    server()
