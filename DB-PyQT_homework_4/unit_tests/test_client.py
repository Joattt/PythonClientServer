import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from client import compose_presence, parse_response


class TestClient(unittest.TestCase):
    def test_ok_presence(self):
        presence = compose_presence()
        presence['time'] = 1.1
        self.assertEqual(presence, {'action': 'presence', 'time': 1.1, 'type': 'status', 'user': {
            'account_name': 'Guest', 'status': 'Hi, I am here!'}})

    def test_ok_response(self):
        self.assertEqual(parse_response({'response': 200}), '200')

    def test_bad_response(self):
        self.assertEqual(parse_response({'response': 400}), '400')

    def test_no_response(self):
        self.assertRaises(ValueError, parse_response, 'error')
