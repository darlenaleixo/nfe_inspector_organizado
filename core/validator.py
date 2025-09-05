# -*- coding: utf-8 -*-
import os
from lxml import etree
from typing import Tuple, Optional

# --- CAMINHO PARA A PASTA DE SCHEMAS ---
# O programa irá procurar por uma pasta chamada 'schemas' dentro do diretório do projeto.
CAMINHO_PASTA_SCHEMAS = os.path.join(os.path.dirname(__file__), '..', 'schemas')

# Mapeamento de versões de NFe para os seus respectivos arquivos XSD
MAPA_XSD = {
    "4.00": "nfe_v4.00.xsd",
    # Adicionar outros mapeamentos se necessário (ex: "3.10": "nfe_v3.10.xsd")
}

def _encontrar_versao_e_schema(root: etree._Element) -> Optional[str]:
    """Encontra a versão da NFe no XML para determinar qual XSD usar."""
    # A tag <infNFe> contém o atributo de versão
    infNFe = root.find(".//{http://www.portalfiscal.inf.br/nfe}infNFe")
    if infNFe is not None:
        versao = infNFe.get("versao")
        if versao and versao in MAPA_XSD:
            return os.path.join(CAMINHO_PASTA_SCHEMAS, MAPA_XSD[versao])
    return None

def validar_com_xsd(caminho_xml: str) -> Tuple[bool, str]:
    """
    Valida um arquivo XML de NFe/NFCe contra o schema XSD oficial da SEFAZ.
    A função agora encontra a versão da NFe e seleciona o XSD correspondente automaticamente.
    """
    if not os.path.exists(CAMINHO_PASTA_SCHEMAS):
        return True, "AVISO: Pasta 'schemas' não encontrada. Validação XSD pulada."

    try:
        xml_doc = etree.parse(caminho_xml)
        raiz_xml = xml_doc.getroot()

        # A validação deve ser feita no elemento <NFe>, não no <nfeProc> que o envolve.
        elemento_para_validar = raiz_xml.find(".//{http://www.portalfiscal.inf.br/nfe}NFe")
        if elemento_para_validar is None:
            # Se não encontrar <NFe>, tenta validar a raiz (caso seja um XML "puro")
            elemento_para_validar = raiz_xml

        caminho_xsd = _encontrar_versao_e_schema(elemento_para_validar)
        if not caminho_xsd:
            return False, "Não foi possível determinar a versão da NFe para validação."
        
        if not os.path.exists(caminho_xsd):
            return False, f"Arquivo de Schema XSD não encontrado: {caminho_xsd}"

        schema_doc = etree.parse(caminho_xsd)
        schema = etree.XMLSchema(schema_doc)
        
        # Valida apenas o elemento <NFe> e seus filhos
        schema.assertValid(etree.ElementTree(elemento_para_validar))
        return True, "Válido"

    except etree.XMLSyntaxError as e:
        return False, f"Erro de sintaxe XML: {e}"
    except etree.DocumentInvalid as e:
        return False, f"Documento inválido (XSD): {e}"
    except Exception as e:
        return False, f"Erro inesperado na validação: {e}"

