import sys
import os
import unittest
import json
sys.path.insert(0, os.path.join(os.getcwd(), '..'))
from common.variables import ENCODING
from common.utils import get_data, send_data


class TestSocket:
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.received_message = None

    def send(self, message):
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.received_message = message

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    test_sent_dict = {
        'action': 'presence',
        'time': 1.1,
        'type': 'status',
        'user': {
            'account_name': 'Guest',
            'status': 'Hi, I am here!'
        }
    }
    test_received_dict_ok = {
        'response': 200,
        'time': 1.1,
        'alert': 'Ok, I see you!'
    }
    test_received_dict_bad = {
        'response': 400,
        'time': 1.1,
        'alert': 'Bad Request'
    }

    def test_send_message_ok(self):
        test_socket = TestSocket(self.test_sent_dict)
        send_data(self.test_sent_dict, test_socket)
        self.assertEqual(test_socket.encoded_message, test_socket.received_message)

    def test_send_message_error(self):
        test_socket = TestSocket(self.test_sent_dict)
        send_data(self.test_sent_dict, test_socket)
        self.assertRaises(TypeError, send_data, test_socket, 'error')

    def test_get_message_ok(self):
        test_sock_ok = TestSocket(self.test_received_dict_ok)
        self.assertEqual(get_data(test_sock_ok), self.test_received_dict_ok)

    def test_get_message_error(self):
        test_sock_err = TestSocket(self.test_received_dict_bad)
        self.assertEqual(get_data(test_sock_err), self.test_received_dict_bad)
