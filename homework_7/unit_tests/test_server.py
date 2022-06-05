import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import compose_confirmation


class TestServer(unittest.TestCase):
    ok_response = {
        'response': 200,
        'time': 1.1,
        'alert': 'Ok, I see you!'
    }
    bad_response = {
        'response': 400,
        'time': 1.1,
        'alert': 'Bad Request'
    }

    def test_ok_response(self):
        response = compose_confirmation({'action': 'presence', 'time': 1.1, 'type': 'status', 'user':
            {'account_name': 'Guest', 'status': 'Hi, I am here!'}})
        response['time'] = 1.1
        self.assertEqual(response, self.ok_response)

    def test_no_action(self):
        response = compose_confirmation({'time': 1.1, 'type': 'status', 'user':
            {'account_name': 'Guest', 'status': 'Hi, I am here!'}})
        response['time'] = 1.1
        self.assertEqual(response, self.bad_response)

    def test_incorrect_action(self):
        response = compose_confirmation({'action': 'no_presence', 'time': 1.1, 'type': 'status', 'user':
            {'account_name': 'Guest', 'status': 'Hi, I am here!'}})
        response['time'] = 1.1
        self.assertEqual(response, self.bad_response)

    def test_no_time(self):
        response = compose_confirmation({'action': 'presence', 'type': 'status', 'user':
            {'account_name': 'Guest', 'status': 'Hi, I am here!'}})
        response['time'] = 1.1
        self.assertEqual(response, self.bad_response)

    def test_no_user(self):
        response = compose_confirmation({'action': 'no_presence', 'time': 1.1, 'type': 'status'})
        response['time'] = 1.1
        self.assertEqual(response, self.bad_response)

    def test_incorrect_user(self):
        response = compose_confirmation({'action': 'no_presence', 'time': 1.1, 'type': 'status', 'user':
            {'account_name': 'not_Guest', 'status': 'Hi, I am here!'}})
        response['time'] = 1.1
        self.assertEqual(response, self.bad_response)
