# sefaz_integration/auth.py
# -*- coding: utf-8 -*-

import os
import ssl
import tempfile
from typing import Tuple
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives import serialization
from .exceptions import CertificateError

class CertificateManager:
    """
    Gerencia a extração de certificado digital (.pfx/.p12) para uso em requisições HTTPS.
    """
    def __init__(self, pfx_path: str, password: str):
            self.pfx_path = pfx_path
            self.password = password
            self._cert_file = None
            self._key_file = None

    def get_cert_files(self) -> Tuple[str, str]:
        """
        Extrai o certificado e a chave privada do PFX e retorna os paths de .pem.
        """
        if self._cert_file and self._key_file:
            return self._cert_file, self._key_file

        try:
            # Carrega dados PKCS#12
            with open(self.pfx_path, 'rb') as f:
                pfx_data = f.read()
                private_key, certificate, _ = pkcs12.load_key_and_certificates(
                pfx_data,
                self.password.encode('utf-8')
            )
            # Cria arquivos temporários
            cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
            key_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')

            # Escreve certificado
            cert_pem = certificate.public_bytes(Encoding.PEM)
            cert_tmp.write(cert_pem)
            cert_tmp.close()

            # Escreve chave privada
            key_pem = private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption()
            )
            key_tmp.write(key_pem)
            key_tmp.close()

            # Armazena para chamadas futuras
            self._cert_file = cert_tmp.name
            self._key_file = key_tmp.name

            return self._cert_file, self._key_file

        except Exception as e:
            raise CertificateError(f"Falha ao extrair certificado: {e}")

    def cleanup(self):
        """
        Remove os arquivos temporários gerados.
        """
        for path in (self._cert_file, self._key_file):
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except OSError:
                pass
