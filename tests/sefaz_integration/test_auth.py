# tests/sefaz_integration/test_auth.py

import os
import tempfile
import pytest
from sefaz_integration.auth import CertificateManager, CertificateError

from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

class DummyKey:
    def private_bytes(self, encoding, format, encryption_algorithm):
        return b"key"

class DummyCert:
    def public_bytes(self, encoding):
        return b"cert"

@pytest.fixture(autouse=True)
def fake_pkcs12(monkeypatch):
    def fake_load(data, pwd):
        return DummyKey(), DummyCert(), None
    monkeypatch.setattr(pkcs12, "load_key_and_certificates", fake_load)
    yield

def test_get_cert_files_invalid_path(tmp_path):
    fake = str(tmp_path / "nao_existe.pfx")
    cm = CertificateManager(fake, "senhaqualquer")
    with pytest.raises(CertificateError):
        cm.get_cert_files()

def test_get_cert_files_success(tmp_path):
    # Gera um arquivo vazio que será "lido" pelo fake
    pfx = tmp_path / "teste.pfx"
    pfx.write_bytes(b"dummy")
    cm = CertificateManager(str(pfx), "senha")
    cert_path, key_path = cm.get_cert_files()
    # Arquivos devem existir
    assert os.path.exists(cert_path)
    assert os.path.exists(key_path)
    # Cleanup remove os temporários
    cm.cleanup()
    assert not os.path.exists(cert_path)
    assert not os.path.exists(key_path)
