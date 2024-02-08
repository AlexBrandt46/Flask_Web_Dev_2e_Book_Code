""" Password Hashing Tests """

import unittest
from app.models import User

class UserModelTestCase(unittest.TestCase):
    """ Class to handle app.models.User test cases
    Inherited from unittest.TestCase
    """

    def test_password_setter(self):
        """ Test to validate that a user's password is hashed on initialization """
        u = User(password = 'cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        """ Test to validate that the User.password property isn't accessible and an AttributeError is raised when its getter is called """
        u = User(password = 'cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        """ Test to validate that password verification is working properly for the given user """
        u = User(password = 'cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))
        
    def test_password_salts_are_random(self):
        """ Test to validate that hashed values aren't the same with 2 of the same string """
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)
    