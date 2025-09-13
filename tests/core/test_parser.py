import pytest
from core.parser import parse_nfe_nfce_xml

@pytest.fixture
def xml_autorizada(tmp_path):
    content = '''<?xml version="1.0"?>
    <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
      <infNFe Id="NFe123"><ide><nNF>1</nNF></ide>
      <emit><CNPJ>123</CNPJ><xNome>Teste</xNome></emit>
      <dest><CPF>11122233344</CPF><xNome>Cliente</xNome></dest>
      <det nItem="1"><prod><cProd>001</cProd><xProd>Item</xProd>
        <qCom>2</qCom><vUnCom>10.00</vUnCom><vProd>20.00</vProd></prod>
      </det>
      <total><ICMSTot><vNF>20.00</vNF><vProd>20.00</vProd></ICMSTot></total>
      <pag><detPag><tPag>01</tPag><vPag>20.00</vPag></detPag></pag>
    </infNFe>
    </NFe>'''
    file = tmp_path / "nota.xml"
    file.write_text(content)
    return str(file)

def test_parse_nfe_valid(xml_autorizada):
    result = parse_nfe_nfce_xml(xml_autorizada, set())
    assert isinstance(result, list)
    assert result[0]["chave_acesso"] == "123"
    assert result[0]["valor_total_nf"] == 20.0

def test_parse_nfe_invalid(tmp_path):
    file = tmp_path / "inválido.xml"
    file.write_text("<xml errado")
    assert parse_nfe_nfce_xml(str(file), set()) is None
