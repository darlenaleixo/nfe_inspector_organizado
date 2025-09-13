import os
import pytest
from lxml import etree
import core.validator as validator

@pytest.fixture(autouse=True)
def prepare_schema(tmp_path, monkeypatch):
    # Cria pasta de schemas em tmp_path
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir(parents=True)
    # Nome de versão conforme MAPA_XSD
    xsd_name = "nfe_v4.00.xsd"
    xsd_file = schema_dir / xsd_name
    xsd_file.write_text("""
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
               targetNamespace="http://www.portalfiscal.inf.br/nfe"
               xmlns="http://www.portalfiscal.inf.br/nfe"
               elementFormDefault="qualified">
      <xs:element name="root"><xs:complexType><xs:sequence>
        <xs:element name="field" type="xs:string"/>
      </xs:sequence></xs:complexType></xs:element>
    </xs:schema>
    """)
    # Monkeypatcha o caminho e o mapa de versões
    monkeypatch.setattr(validator, "C:\nfe_inspector_organizado\schemas", str(schema_dir))
    monkeypatch.setitem(validator.MAPA_XSD, "4.00", xsd_name)

def test_valid_xml(tmp_path):
    xml = tmp_path / "valid.xml"
    xml.write_text("""
    <root xmlns="http://www.portalfiscal.inf.br/nfe">
      <field>value</field>
    </root>
    """)
    valid, msg = validator.validar_com_xsd(str(xml))
    assert valid is True
    assert msg == "Válido"

def test_invalid_xml_missing_element(tmp_path):
    xml = tmp_path / "invalid.xml"
    xml.write_text("""
    <root xmlns="http://www.portalfiscal.inf.br/nfe">
      <wrong>oops</wrong>
    </root>
    """)
    valid, msg = validator.validar_com_xsd(str(xml))
    assert valid is False
    assert "Documento inválido" in msg

def test_invalid_xml_syntax(tmp_path):
    xml = tmp_path / "syntax_error.xml"
    xml.write_text("<root><field>no close")
    valid, msg = validator.validar_com_xsd(str(xml))
    assert valid is False
    assert "Erro de sintaxe" in msg
