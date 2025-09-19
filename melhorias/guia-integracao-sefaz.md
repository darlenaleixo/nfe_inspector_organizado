# Guia Completo: Integração com WebServices SEFAZ para NFe Inspector

## Visão Geral

Este guia mostra como implementar conectividade com os webservices oficiais da SEFAZ para consultas online de NFe/NFCe no seu projeto NFe Inspector Organizado.

## Estrutura da Integração

### 1. Arquivos Necessários

```
sefaz_integration/
├── __init__.py
├── client.py          # Cliente principal SEFAZ
├── auth.py           # Autenticação com certificado
├── config.py         # Configurações e endpoints
├── parsers.py        # Processadores de resposta XML
└── exceptions.py     # Exceções customizadas
```

### 2. Dependências Adicionais

Adicione ao seu `requirements.txt`:

```
zeep>=4.2.1
cryptography>=3.4.8
pyopenssl>=21.0.0
requests>=2.28.0
lxml>=4.6.0
```

## Implementação Principal

### Client Principal (sefaz_integration/client.py)

```python
# -*- coding: utf-8 -*-
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging
from .auth import CertificateManager
from .config import SefazConfig
from .parsers import ResponseParser
from .exceptions import SefazError, CertificateError

class SefazWebserviceClient:
    """
    Cliente para integração com webservices da SEFAZ
    Suporta consultas de status, NFe por chave e distribuição DFe
    """
    
    def __init__(self, uf: str, cert_path: str, cert_password: str, homolog: bool = True):
        self.uf = uf.upper()
        self.homolog = homolog
        self.ambiente = 2 if homolog else 1
        
        # Gerenciadores
        self.cert_manager = CertificateManager(cert_path, cert_password)
        self.config = SefazConfig()
        self.parser = ResponseParser()
        
        # Configurar sessão HTTP
        self.session = self._create_session()
        
        # Logger
        self.logger = logging.getLogger(f'sefaz.{uf}')
        
    def _create_session(self) -> requests.Session:
        """Cria sessão HTTP com certificado digital"""
        session = requests.Session()
        
        # Configurar certificado
        cert_files = self.cert_manager.get_cert_files()
        session.cert = cert_files
        
        # Headers padrão
        session.headers.update({
            'User-Agent': 'NFe Inspector/1.0',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        
        return session
        
    def consultar_status_servico(self) -> Dict:
        """
        Consulta status do webservice da SEFAZ
        
        Returns:
            dict: Status do serviço com informações de disponibilidade
        """
        try:
            xml_request = self._build_status_xml()
            url = self.config.get_service_url(self.uf, 'status', self.homolog)
            
            response = self._send_soap_request(url, 'NFeStatusServico4', xml_request)
            return self.parser.parse_status_response(response)
            
        except Exception as e:
            self.logger.error(f"Erro na consulta status: {e}")
            raise SefazError(f"Falha na consulta status: {str(e)}")
    
    def consultar_nfe_por_chave(self, chave_acesso: str) -> Dict:
        """
        Consulta NFe pela chave de acesso
        
        Args:
            chave_acesso (str): Chave de 44 dígitos
            
        Returns:
            dict: Dados completos da NFe
        """
        if not self._validar_chave_acesso(chave_acesso):
            raise ValueError("Chave de acesso inválida")
            
        try:
            xml_request = self._build_consulta_xml(chave_acesso)
            url = self.config.get_service_url(self.uf, 'consulta', self.homolog)
            
            response = self._send_soap_request(url, 'NFeConsultaProtocolo4', xml_request)
            return self.parser.parse_consulta_response(response, chave_acesso)
            
        except Exception as e:
            self.logger.error(f"Erro consultando NFe {chave_acesso}: {e}")
            raise SefazError(f"Falha na consulta NFe: {str(e)}")
    
    def consultar_distribuicao_dfe(self, cnpj: str, nsu: int = 0) -> Dict:
        """
        Consulta distribuição de documentos fiscais eletrônicos
        
        Args:
            cnpj (str): CNPJ do interessado
            nsu (int): Número sequencial único (0 para todos)
            
        Returns:
            dict: Lista de documentos disponíveis
        """
        try:
            xml_request = self._build_distribuicao_xml(cnpj, nsu)
            url = self.config.get_distribuicao_url(self.homolog)
            
            response = self._send_soap_request(
                url, 'nfeDistDFeInteresse', xml_request
            )
            
            return self.parser.parse_distribuicao_response(response)
            
        except Exception as e:
            self.logger.error(f"Erro na distribuição DFe para {cnpj}: {e}")
            raise SefazError(f"Falha na consulta distribuição: {str(e)}")
    
    def _build_status_xml(self) -> str:
        """Constrói XML para consulta de status"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
            <soap:Header/>
            <soap:Body>
                <nfeStatusServicoNF xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4">
                    <nfeDadosMsg>
                        <consStatServ xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
                            <tpAmb>{self.ambiente}</tpAmb>
                            <cUF>{self.config.get_codigo_uf(self.uf)}</cUF>
                            <xServ>STATUS</xServ>
                        </consStatServ>
                    </nfeDadosMsg>
                </nfeStatusServicoNF>
            </soap:Body>
        </soap:Envelope>'''
    
    def _build_consulta_xml(self, chave: str) -> str:
        """Constrói XML para consulta por chave"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
            <soap:Header/>
            <soap:Body>
                <nfeConsultaNF xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
                    <nfeDadosMsg>
                        <consSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
                            <tpAmb>{self.ambiente}</tpAmb>
                            <xServ>CONSULTAR</xServ>
                            <chNFe>{chave}</chNFe>
                        </consSitNFe>
                    </nfeDadosMsg>
                </nfeConsultaNF>
            </soap:Body>
        </soap:Envelope>'''
    
    def _send_soap_request(self, url: str, action: str, xml_data: str) -> str:
        """Envia requisição SOAP para SEFAZ"""
        headers = {
            'SOAPAction': f'http://www.portalfiscal.inf.br/nfe/wsdl/{action}'
        }
        
        try:
            response = self.session.post(
                url, 
                data=xml_data, 
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.Timeout:
            raise SefazError("Timeout na requisição SEFAZ")
        except requests.exceptions.SSLError as e:
            raise CertificateError(f"Erro de certificado: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise SefazError(f"Erro na requisição: {str(e)}")
    
    def _validar_chave_acesso(self, chave: str) -> bool:
        """Valida formato da chave de acesso"""
        return (
            isinstance(chave, str) and 
            len(chave) == 44 and 
            chave.isdigit()
        )
```

### Gerenciador de Certificados (sefaz_integration/auth.py)

```python
# -*- coding: utf-8 -*-
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
import tempfile
import os
from typing import Tuple
from .exceptions import CertificateError

class CertificateManager:
    """Gerenciador de certificados digitais para autenticação SEFAZ"""
    
    def __init__(self, cert_path: str, password: str):
        self.cert_path = cert_path
        self.password = password
        self._cert_files = None
        
    def get_cert_files(self) -> Tuple[str, str]:
        """
        Extrai certificado e chave privada do arquivo .pfx
        
        Returns:
            tuple: (caminho_cert.pem, caminho_key.pem)
        """
        if self._cert_files is None:
            self._cert_files = self._extract_from_pfx()
        
        return self._cert_files
    
    def _extract_from_pfx(self) -> Tuple[str, str]:
        """Extrai certificado e chave do arquivo .pfx/.p12"""
        try:
            with open(self.cert_path, 'rb') as f:
                pfx_data = f.read()
            
            # Carregar PKCS#12
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data, 
                self.password.encode('utf-8')
            )
            
            # Criar arquivos temporários
            cert_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.pem', delete=False)
            key_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.key', delete=False)
            
            # Escrever certificado
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
            cert_file.write(cert_pem)
            cert_file.close()
            
            # Escrever chave privada
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            key_file.write(key_pem)
            key_file.close()
            
            return (cert_file.name, key_file.name)
            
        except Exception as e:
            raise CertificateError(f"Erro ao processar certificado: {str(e)}")
    
    def cleanup(self):
        """Remove arquivos temporários de certificado"""
        if self._cert_files:
            for file_path in self._cert_files:
                try:
                    os.unlink(file_path)
                except OSError:
                    pass
            self._cert_files = None
```

## Integração com NFe Inspector

### Modificações no Processor Principal

Adicione ao seu `processing/processor.py`:

```python
from sefaz_integration.client import SefazWebserviceClient
from sefaz_integration.exceptions import SefazError

class NFeProcessor:
    def __init__(self, pasta_xml: str, pasta_saida: str):
        # ... código existente ...
        self.sefaz_clients = {}  # Cache de clientes SEFAZ
    
    def get_sefaz_client(self, uf: str) -> Optional[SefazWebserviceClient]:
        """Obtém cliente SEFAZ para UF específico"""
        if not self._sefaz_config_exists():
            return None
            
        if uf not in self.sefaz_clients:
            try:
                config = self._load_sefaz_config()
                self.sefaz_clients[uf] = SefazWebserviceClient(
                    uf=uf,
                    cert_path=config['certificado_path'],
                    cert_password=config['senha_certificado'],
                    homolog=config.get('homologacao', True)
                )
            except Exception as e:
                logging.error(f"Erro ao criar cliente SEFAZ {uf}: {e}")
                return None
                
        return self.sefaz_clients[uf]
    
    def consultar_nfes_online(self, chaves: List[str]) -> Dict:
        """Consulta NFes online via SEFAZ"""
        resultados = {}
        
        # Agrupar chaves por UF (primeiros 2 dígitos)
        chaves_por_uf = self._agrupar_chaves_por_uf(chaves)
        
        for uf, chaves_uf in chaves_por_uf.items():
            client = self.get_sefaz_client(uf)
            if not client:
                continue
                
            resultados[uf] = []
            for chave in chaves_uf:
                try:
                    resultado = client.consultar_nfe_por_chave(chave)
                    resultados[uf].append(resultado)
                except SefazError as e:
                    resultados[uf].append({'erro': str(e), 'chave': chave})
                    
        return resultados
    
    def verificar_status_sefaz(self) -> Dict:
        """Verifica status dos webservices SEFAZ"""
        ufs_detectados = self._detectar_ufs_processados()
        status_geral = {}
        
        for uf in ufs_detectados:
            client = self.get_sefaz_client(uf)
            if client:
                try:
                    status = client.consultar_status_servico()
                    status_geral[uf] = status
                except Exception as e:
                    status_geral[uf] = {'status': 'erro', 'motivo': str(e)}
                    
        return status_geral
    
    def _load_sefaz_config(self) -> Dict:
        """Carrega configurações SEFAZ"""
        # Implementar carregamento das configurações
        pass
```

## Configuração

### Arquivo de Configuração (config_sefaz.ini)

```ini
[CERTIFICADO]
# Caminho para o certificado digital (.pfx/.p12)
caminho = /path/to/certificado.pfx
senha = sua_senha_aqui

[AMBIENTE]
# true para homologação, false para produção
homologacao = true

[TIMEOUTS]
# Timeout para requisições (segundos)
request_timeout = 30
connection_timeout = 10

[CACHE]
# Cache de status de serviço (minutos)
cache_status_minutos = 5

[LOGS]
# Nível de log para SEFAZ
nivel = INFO
arquivo = logs/sefaz.log
```

## Uso Prático

### 1. Consulta Simples

```python
from sefaz_integration.client import SefazWebserviceClient

# Criar cliente
client = SefazWebserviceClient(
    uf='PR',
    cert_path='certificado.pfx',
    cert_password='senha123',
    homolog=True
)

# Consultar status
status = client.consultar_status_servico()
print(f"SEFAZ Status: {status['status']}")

# Consultar NFe
chave = "41210114200166000187550010000000021123456789"
nfe = client.consultar_nfe_por_chave(chave)
print(f"NFe: {nfe['numero']} - {nfe['valor_total']}")
```

### 2. Integração com Dashboard Web

Adicione ao seu `ui/web.py`:

```python
@app.route('/api/sefaz/status')
def api_sefaz_status():
    """API endpoint para status SEFAZ"""
    try:
        processor = app.processor
        status = processor.verificar_status_sefaz()
        return jsonify(status)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/sefaz/consultar', methods=['POST'])
def api_sefaz_consultar():
    """API endpoint para consulta online"""
    try:
        data = request.get_json()
        chaves = data.get('chaves', [])
        
        processor = app.processor
        resultados = processor.consultar_nfes_online(chaves)
        
        return jsonify(resultados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
```

## Vantagens da Implementação

1. **Validação em Tempo Real**: Confirma se NFes estão realmente autorizadas
2. **Detecção de Cancelamentos**: Identifica NFes canceladas após emissão
3. **Dados Atualizados**: Obtém informações mais recentes que XMLs locais
4. **Auditoria Completa**: Permite comparação entre dados locais e SEFAZ
5. **Status de Serviços**: Monitora disponibilidade dos webservices

## Considerações Importantes

### Segurança
- Certificado digital obrigatório
- Senhas devem ser criptografadas em produção
- Logs não devem conter informações sensíveis

### Performance
- Implementar cache para evitar consultas duplicadas
- Limitar número de consultas simultâneas
- Rate limiting para evitar bloqueio por abuso

### Tratamento de Erros
- Retry automático para falhas temporárias
- Fallback para dados locais quando SEFAZ indisponível
- Logging detalhado para debugging

Esta implementação fornece uma base sólida para integração completa com os webservices oficiais da SEFAZ, mantendo compatibilidade com sua arquitetura existente do NFe Inspector.