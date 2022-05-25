from socket import socket, AF_INET, SOCK_STREAM
import json
import time
import sys
from common.utils import get_data, send_data
from common.variables import DEFAULT_ADDRESS, DEFAULT_PORT


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
    return presence


def parse_response(response):
    if 'response' in response:
        if response['response'] == 200:
            return '200'
        return '400'
    return ValueError


def client():
    try:
        addr = DEFAULT_ADDRESS if len(sys.argv) <= 1 else sys.argv[1]
        port = DEFAULT_PORT if len(sys.argv) <= 2 else int(sys.argv[2])
        if port < 1024 or port > 65535:
            raise ValueError
    except ValueError:
        print('Портом может быть только число в диапазоне от 1024 до 65535.')
    client_sock = socket(AF_INET, SOCK_STREAM)
    client_sock.connect((addr, port))
    send_data(compose_presence(), client_sock)
    print(f'На сервер отправлено сообщение: {compose_presence()}')
    try:
        response = parse_response(get_data(client_sock))
        print(f'С сервера получен ответ: {response}\n')
        client_sock.close()
    except (ValueError, json.JSONDecodeError):
        print('Не удалось декодировать сообщение сервера.')
        client_sock.close()


if __name__ == '__main__':
    client()
