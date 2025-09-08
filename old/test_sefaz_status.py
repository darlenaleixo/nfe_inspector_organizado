# test_sefaz_status.py

import requests
from lxml import etree
from sefaz_integration.auth import CertificateManager

def test_sefaz_status():
    pfx_path = r"C:\nfe_inspector_organizado\CERT DUDAS REST 2025.pfx"
    password = "1234"

    cert_manager = CertificateManager(pfx_path, password)
    cert_file, key_file = cert_manager.get_cert_files()

    # Apenas o XML de consulta de status, sem espaços desnecessários
    cons_stat = (
        '<consStatServ xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
        '<tpAmb>2</tpAmb>'
        '<cUF>33</cUF>'
        '<xServ>STATUS</xServ>'
        '</consStatServ>'
    )

    # Envelope SOAP 1.1, com <nfeDadosMsg> NO NAMESPACE do serviço
    xml_status = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soapenv:Envelope '
            'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4">'
            '<soapenv:Header/>'
            '<soapenv:Body>'
                '<nfeDadosMsg><![CDATA[' + cons_stat + ']]></nfeDadosMsg>'
            '</soapenv:Body>'
        '</soapenv:Envelope>'
    )

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4/nfeStatusServicoNF'
    }

    url = "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx"

    session = requests.Session()
    session.cert = (cert_file, key_file)
    session.verify = r"C:\nfe_inspector_organizado\svrs_chain.pem"

    print("🔄 Testando status do serviço SEFAZ (SOAP 1.1 + CDATA, minimal payload)...")
    try:
        response = session.post(url, data=xml_status, headers=headers, timeout=15)
        print(f"✅ Status HTTP: {response.status_code}")

        if response.status_code != 200:
            print("❌ Falha na requisição SOAP (código diferente de 200).")
            return False

        root = etree.fromstring(response.content)
        # Namespace para elementos de resposta
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        cStat = root.findtext('.//nfe:cStat', namespaces=ns)
        xMotivo = root.findtext('.//nfe:xMotivo', namespaces=ns)

        print(f"✅ Código SEFAZ Serviço: {cStat}")
        print(f"✅ Motivo: {xMotivo}")

        if cStat == "107":
            print("🎉 Serviço SEFAZ está ONLINE (107).")
            return True
        else:
            print("⚠️ Serviço SEFAZ retornou outro código.")
            return False

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    if test_sefaz_status():
        print("✅ Teste de status PASSOU!")
    else:
        print("❌ Teste de status FALHOU.")
