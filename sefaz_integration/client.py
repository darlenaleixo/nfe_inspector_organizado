# -*- coding: utf-8 -*-
import logging
import ssl
import warnings
from lxml import etree
from requests import Session
from requests.adapters import HTTPAdapter
import certifi
from zeep import Client, Settings, Transport
from zeep.exceptions import Fault
from core.config import config_manager

# --- Adaptador de Conexão Customizado ---
class TlsHttpAdapter(HTTPAdapter):
    """Adaptador para forçar o uso de TLS >=1.2."""
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        # Contexto de CLIENTE
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2  # mínimo TLS 1.2

        from urllib3.poolmanager import PoolManager
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ssl_context,
            **pool_kwargs
        )

# --- Endereços dos Webservices ---
ENDPOINTS = {
    'RJ': {
        'producao': 'https://nfe.fazenda.rj.gov.br/NFeConsulta/NFeConsulta4.asmx?WSDL',
        'homologacao': 'https://nfe-homologacao.svrs.rs.gov.br/ws/NfeConsulta/NFeConsulta4.asmx?WSDL'
    }
}

class SefazClient:
    """Cliente para consulta de NFe nos webservices da SEFAZ."""
    def __init__(self, cert_pem: str, key_pem: str):
        self.uf = config_manager.get('SEFAZ', 'uf', 'RJ')
        self.ambiente = 'producao' if config_manager.get('SEFAZ', 'ambiente') == '1' else 'producao'
        self.cert_pem = cert_pem
        self.key_pem = key_pem
        self.wsdl = ENDPOINTS.get(self.uf, {}).get(self.ambiente)
        self.verificar_ssl = config_manager.getboolean('SEFAZ', 'verificar_ssl', fallback=True)
        
        if not self.wsdl:
            raise ValueError(f"Endpoint da SEFAZ não encontrado para UF: {self.uf} e Ambiente: {self.ambiente}")

    def consultar_chave(self, chave_acesso: str) -> dict:
        """Consulta o status de uma única chave de acesso na SEFAZ."""
        if len(chave_acesso) != 44 or not chave_acesso.isdigit():
            return {'status': 'Erro', 'motivo': 'Chave de acesso inválida'}
        
        
        try:
        
            session = Session()
            session.cert = (self.cert_pem, self.key_pem)
            
            # Monta o adaptador TLS
            session.mount("https://", TlsHttpAdapter())
            
            if self.verificar_ssl:
                session.verify = certifi.where()
            else:
                session.verify = False
                warnings.filterwarnings("ignore", message="Unverified HTTPS request")
                logging.warning("A verificação de certificado SSL da SEFAZ está DESABILITADA.")

            transport = Transport(session=session)
            settings = Settings(strict=False, xml_huge_tree=True)
            client = Client(self.wsdl, transport=transport, settings=settings)

            versao = "4.00"
            servico = "CONSULTAR"
            ns = "http://www.portalfiscal.inf.br/nfe"
            
            xml_payload = f"""
            <consSitNFe xmlns="{ns}" versao="{versao}">
                <tpAmb>{config_manager.get('SEFAZ', 'ambiente')}</tpAmb>
                <xServ>{servico}</xServ>
                <chNFe>{chave_acesso}</chNFe>
            </consSitNFe>
            """
            payload_element = etree.fromstring(xml_payload)
            
            response = client.service.nfeConsultaNF(nfeDadosMsg=payload_element)

            if response:
                return self._parse_response(response)
            return {'status': 'Erro', 'motivo': 'Resposta vazia da SEFAZ'}

        except Fault as e:
            logging.error(f"Erro na consulta à SEFAZ (Fault): {e.message}")
            return {'status': 'Erro SOAP', 'motivo': str(e.message)}
        except Exception as e:
            logging.error(f"Erro inesperado na consulta à SEFAZ: {e}", exc_info=True)
            return {'status': 'Erro Inesperado', 'motivo': str(e)}


    def _parse_response(self, response: etree.Element) -> dict:
        """Interpreta a resposta XML da SEFAZ."""
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        cStat = response.findtext('.//nfe:cStat', namespaces=ns)
        xMotivo = response.findtext('.//nfe:xMotivo', namespaces=ns)
        return {'Código de Status': cStat, 'Motivo': xMotivo}
