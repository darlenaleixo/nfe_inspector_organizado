from cryptography.hazmat.primitives.serialization import pkcs12
from datetime import datetime

class CertificateManager:
    def __init__(self, path, password):
        self.path = path
        self.password = password.encode()
        self.cert, self.key, _ = self._load_pfx()

    def _load_pfx(self):
        data = open(self.path, "rb").read()
        return pkcs12.load_key_and_certificates(data, self.password)

    def get_expiration_date(self):
        return self.cert.not_valid_after

    def days_until_expiration(self):
        delta = self.get_expiration_date() - datetime.utcnow()
        return delta.days
