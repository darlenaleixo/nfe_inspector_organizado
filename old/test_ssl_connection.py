# test_ssl_connection.py
import requests
from sefaz_integration.auth import CertificateManager

def test_ssl_connection():
    pfx_path = r"C:\nfe_inspector_organizado\CERT DUDAS REST 2025.pfx"
    password = "1234"

    cert_manager = CertificateManager(pfx_path, password)
    cert_file, key_file = cert_manager.get_cert_files()

    session = requests.Session()
    session.cert = (cert_file, key_file)
    # Aponte para o seu CA customizado que inclui o SVRS
    session.verify = r"C:\nfe_inspector_organizado\svrs_chain.pem"

    try:
        url = "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeConsulta/NFeConsulta4.asmx?WSDL"
        response = session.get(url, timeout=10)
        print(f"✅ Status HTTP: {response.status_code}")
        print(f"✅ Tamanho da resposta: {len(response.content)} bytes")
        return True

    except requests.exceptions.SSLError as e:
        print(f"❌ Erro SSL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    assert test_ssl_connection() is True
