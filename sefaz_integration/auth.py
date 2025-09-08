# -*- coding: utf-8 -*-
import os
import ssl
import tempfile
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import logging

class CertificateManager:
    """Gerencia o carregamento e o uso de certificados digitais A1."""
    def __init__(self, pfx_path: str, password: str):
        if not os.path.exists(pfx_path):
            raise FileNotFoundError(f"Arquivo de certificado não encontrado em: {pfx_path}")
        self.pfx_path = pfx_path
        self.password = password.encode('utf-8')
        self.cert_file = None
        self.key_file = None

    def load_and_prepare_files(self) -> ssl.SSLContext:
        """
        Carrega o arquivo PFX, extrai a chave e o certificado,
        e os salva em arquivos temporários para uso pelo Zeep.
        """
        try:
            with open(self.pfx_path, 'rb') as f:
                pfx_data = f.read()
            
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                pfx_data, self.password
            )

            # Salva a chave privada em um arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, mode='wb', suffix='.key') as key_temp:
                self.key_file = key_temp.name
                key_temp.write(private_key.private_bytes(
                    Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
                ))

            # Salva o certificado em um arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, mode='wb', suffix='.crt') as cert_temp:
                self.cert_file = cert_temp.name
                cert_temp.write(certificate.public_bytes(Encoding.PEM))

            # Cria o contexto SSL para a requisição
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
            return context

        except Exception as e:
            logging.error(f"Erro ao carregar o certificado: {e}")
            self.cleanup()
            raise

    def cleanup(self):
        """Remove os arquivos temporários de chave e certificado."""
        if self.cert_file and os.path.exists(self.cert_file):
            os.remove(self.cert_file)
        if self.key_file and os.path.exists(self.key_file):
            os.remove(self.key_file)
