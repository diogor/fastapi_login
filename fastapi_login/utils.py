import os
import hashlib
from base64 import b64encode


def make_password(password: str) -> (str, str):
    """
    :param str password: The plain text user provided password
    :return: A tuple containing the encrypted password string, and the salt
    """
    salt = b64encode(os.urandom(32)).decode('utf-8')
    password = b64encode(
        hashlib.pbkdf2_hmac('sha256',
                            password.encode(),
                            salt.encode(),
                            100000)).decode('utf-8')
    return (password, salt)

def check_password(encrypted_password: str, salt: str, password: str) -> bool:
    """
    :param str encrypted_password: The stored encrypted password
    :param str salt: The salt that was used for the encryption process
    :param str password: The plain text user provided password
    :return: True or False
    """
    key = b64encode(hashlib.pbkdf2_hmac(
                    'sha256', password.encode(),
                    salt.encode(), 100000)).decode('utf-8')
    return encrypted_password == key
