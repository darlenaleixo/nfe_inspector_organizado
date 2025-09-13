import pytest
from pathlib import Path
import responses

from sefaz_integration.auth import CertificateManager
from sefaz_integration.client import SefazClient, ENDPOINTS_CONSULTA, ENDPOINTS_STATUS

FIXTURES = Path(__file__).parent.parent / "fixtures"

@pytest.fixture(autouse=True)
def fake_cert_files(tmp_path, monkeypatch):
    # Cria arquivos PEM dummy para cert e key
    cert = tmp_path / "cert.pem"
    key  = tmp_path / "key.pem"
    cert.write_bytes(b"dummy_cert")
    key.write_bytes(b"dummy_key")
    # Monkeypatch get_cert_files para não falhar
    monkeypatch.setattr(
        CertificateManager, 
        "get_cert_files", 
        lambda self: (str(cert), str(key))
    )
    return

@pytest.fixture(autouse=True)
def wsdl_fixtures(monkeypatch):
    # Override dos endpoints para usar WSDLs de fixtures
    consulta_wsdl = str(FIXTURES / "wsdl" / "NFeConsulta4.wsdl")
    status_wsdl   = str(FIXTURES / "wsdl" / "NFeStatusServico4.wsdl")
    monkeypatch.setitem(ENDPOINTS_CONSULTA['RJ'], 'homologacao', consulta_wsdl)
    monkeypatch.setitem(ENDPOINTS_STATUS['RJ'],   'homologacao', status_wsdl)
    return

@responses.activate
def test_consultar_chave_mock():
    client = SefazClient("dummy.pfx", "senha", homolog=True)
    url = client.wsdl_consulta.replace("?WSDL", "")
    body = (FIXTURES / "soap_consulta_response.xml").read_text()
    responses.add(responses.POST, url, body=body, status=200, content_type="text/xml")

    res = client.consultar_chave("12345678901234567890123456789012345678901234")
    assert res["Código de Status"] == "100"
    assert "Autorizado" in res["Motivo"]

@responses.activate
def test_status_servico_mock():
    client = SefazClient("dummy.pfx", "senha", homolog=True)
    url = client.wsdl_status.replace("?WSDL", "")
    body = (FIXTURES / "soap_status_response.xml").read_text()
    responses.add(responses.POST, url, body=body, status=200, content_type="text/xml")

    res = client.status_servico()
    assert res["Código de Status"] == "107"
    assert "operacao" in res["Motivo"].lower()
