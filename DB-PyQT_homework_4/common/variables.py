DEFAULT_ADDRESS = '127.0.0.1'
DEFAULT_PORT = 7777
ENCODING = 'utf-8'
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024

RESPONSE_200 = {
    'response': 200,
    'alert': 'Ok, I see you!'
}

RESPONSE_400 = {
    'response': 400,
    'alert': 'Это имя пользователя уже занято.'
}

RESPONSE_202 = {
    'response': 202,
    'data_list': None
}
