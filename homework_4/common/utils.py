import json
from common.variables import ENCODING, MAX_PACKAGE_LENGTH


def get_data(sender):
    message = sender.recv(MAX_PACKAGE_LENGTH)
    if isinstance(message, bytes):
        decoded_message = message.decode(ENCODING)
        if isinstance(decoded_message, str):
            json_message = json.loads(decoded_message)
            if isinstance(json_message, dict):
                return json_message
            raise ValueError
        raise ValueError
    raise ValueError


def send_data(message, recipient):
    if not isinstance(message, dict):
        raise TypeError
    json_message = json.dumps(message)
    encoded_message = json_message.encode(ENCODING)
    recipient.send(encoded_message)
