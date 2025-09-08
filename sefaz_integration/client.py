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

from sefaz_integration.auth import CertificateManager
from core.config import config_manager

# --- Adaptador de Conexão Customizado ---
class TlsHttpAdapter(HTTPAdapter):
    """Adaptador para forçar o uso de TLS >=1.2."""
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
       
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        from urllib3.poolmanager import PoolManager
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ssl_context,
            **pool_kwargs
        )

# --- Endpoints dos Webservices de Consulta e Status ---
from pathlib import Path

BASE = Path(__file__).parent.parent  # raiz do projeto

ENDPOINTS_CONSULTA = {
    'RJ': {
        'producao': 'https://nfe.fazenda.rj.gov.br/NFeConsulta/NFeConsulta4.asmx?WSDL',
        'homologacao': str(BASE / 'NFeConsulta4.wsdl')
    },
    # ... outras UFs ...
}

ENDPOINTS_STATUS = {
    'RJ': {
        'producao': 'https://nfe.fazenda.rj.gov.br/NfeStatusServico/NfeStatusServico4.asmx?WSDL',
        'homologacao': str(BASE / 'NFeStatusServico4.wsdl')
    },
    # ... outras UFs ...
}

class SefazClient:
    """Cliente para consulta de NFe e status de serviço nos webservices da SEFAZ."""
    def __init__(
        self,
        certificado_path: str,
        senha_certificado: str,
        homolog: bool = True
    ):
        # Extrai certificado e chave privada do PFX
        cert_manager = CertificateManager(certificado_path, senha_certificado)
        self.cert_pem, self.key_pem = cert_manager.get_cert_files()

        # Configurações de ambiente
        self.uf = config_manager.get('SEFAZ', 'uf', 'RJ')
        env_flag = config_manager.get('SEFAZ', 'ambiente', fallback='1')
        self.ambiente = 'homologacao' if env_flag == '2' else 'producao'
        self.verificar_ssl = config_manager.getboolean('SEFAZ', 'verificar_ssl', fallback=True)

        # Endpoints
        self.wsdl_consulta = ENDPOINTS_CONSULTA.get(self.uf, {}).get(self.ambiente)
        self.wsdl_status = ENDPOINTS_STATUS.get(self.uf, {}).get(self.ambiente)
        if not self.wsdl_consulta:
            raise ValueError(f"Endpoint de consulta SEFAZ não encontrado: UF={self.uf}, ambiente={self.ambiente}")
        if not self.wsdl_status:
            raise ValueError(f"Endpoint de status SEFAZ não encontrado: UF={self.uf}, ambiente={self.ambiente}")

    def _create_transport(self) -> Transport:
        """Cria o transport do Zeep com certificado cliente e TLS adapter."""
        session = Session()
        session.cert = (self.cert_pem, self.key_pem)
        session.mount("https://", TlsHttpAdapter())
        if self.verificar_ssl:
            session.verify = certifi.where()
        else:
            session.verify = False
            warnings.filterwarnings("ignore", message="Unverified HTTPS request")
            logging.warning("SSL verificação DESABILITADA.")
        return Transport(session=session)

    def consultar_chave(self, chave_acesso: str) -> dict:
        """Consulta o status de uma única chave de acesso na SEFAZ."""
        if len(chave_acesso) != 44 or not chave_acesso.isdigit():
            return {'status': 'Erro', 'motivo': 'Chave de acesso inválida'}

        try:
            transport = self._create_transport()
            settings = Settings(strict=False, xml_huge_tree=True)
            client = Client(self.wsdl_consulta, transport=transport, settings=settings)

            xml_payload = (
                '<consSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
                f'<tpAmb>{"2" if self.ambiente=="homologacao" else "1"}</tpAmb>'
                '<xServ>CONSULTAR</xServ>'
                f'<chNFe>{chave_acesso}</chNFe>'
                '</consSitNFe>'
            )
            payload_element = etree.fromstring(xml_payload)
            
            response = client.service.nfeConsultaNF(nfeDadosMsg=payload_element)

            if response is not None:
                return self._parse_response(response)
            return {'status': 'Erro', 'motivo': 'Resposta vazia da SEFAZ'}

        except Fault as e:
            logging.error(f"Erro SOAP na consulta: {e.message}")
            return {'status': 'Erro SOAP', 'motivo': e.message}
        except Exception as e:
            logging.error(f"Erro inesperado na consulta: {e}", exc_info=True)
            return {'status': 'Erro Inesperado', 'motivo': str(e)}

    def status_servico(self) -> dict:
        """Consulta o status do serviço SEFAZ."""
        try:
            transport = self._create_transport()
            settings = Settings(strict=False, xml_huge_tree=True)
            client = Client(self.wsdl_status, transport=transport, settings=settings)

            # Monta XML de status como string para CDATA
            cons_stat = (
                '<consStatServ xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
                f'<tpAmb>{"2" if self.ambiente=="homologacao" else "1"}</tpAmb>'
                f'<cUF>{config_manager.get("SEFAZ","cUF", self.uf)}</cUF>'
                '<xServ>STATUS</xServ>'
                '</consStatServ>'
            )
            # Usa CDATA para o nfeDadosMsg
            response = client.service.nfeStatusServicoNF(
                nfeDadosMsg=etree.CDATA(cons_stat)
            )
            return self._parse_response(response)

        except Fault as e:
            logging.error(f"Erro SOAP no status: {e.message}")
            return {'status': 'Erro SOAP', 'motivo': e.message}
        except Exception as e:
            logging.error(f"Erro inesperado no status: {e}", exc_info=True)
            return {'status': 'Erro Inesperado', 'motivo': str(e)}

    def _parse_response(self, response: etree.Element) -> dict:
        """Interpreta a resposta XML da SEFAZ."""
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        cStat = response.findtext('.//nfe:cStat', namespaces=ns)
        xMotivo = response.findtext('.//nfe:xMotivo', namespaces=ns)
        return {'Código de Status': cStat, 'Motivo': xMotivo}
