from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes


class Key:
    def __init__(self, key=None, key_length=2048):
        if key:
            self.key = RSA.import_key(key)
        else:
            self.key = RSA.generate(key_length)
        self.public_key = self.key.publickey()

    def export_keys(self):
        private_key = self.key.export_key()
        public_key = self.public_key.export_key()
        return private_key, public_key

    def encrypt(self, plaintext: str) -> bytes:
        cipher = PKCS1_OAEP.new(self.public_key)
        return cipher.encrypt(plaintext.encode('utf-8'))

    def decrypt(self, ciphertext: bytes) -> str:
        cipher = PKCS1_OAEP.new(self.key)
        return cipher.decrypt(ciphertext).decode('utf-8')

    def set_key(self, key: str):
        self.key = key

class PublicKey:
    def __init__(self, key):
        self.public_key = RSA.import_key(key)

    def export_key(self):
        public_key = self.public_key.export_key()
        return public_key

    def encrypt(self, plaintext: str) -> bytes:
        cipher = PKCS1_OAEP.new(self.public_key)
        return cipher.encrypt(plaintext.encode('utf-8'))

    def set_key(self, key: str):
        self.public_key = public_key