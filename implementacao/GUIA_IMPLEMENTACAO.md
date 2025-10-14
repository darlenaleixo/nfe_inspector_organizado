# 📚 Guia Completo de Implementação - Sistema de Download NFe/NFSe

## 🚀 Implementação Passo a Passo

### 1. Preparação do Ambiente

#### 1.1 Organização das Pastas
```bash
cd seu_projeto_nfe_inspector_organizado/

# Criar estrutura para novos módulos
mkdir -p download
mkdir -p sefaz
mkdir -p schemas

# Mover arquivos existentes se necessário
# (auth.py e client.py já existem, mas vamos atualizar)
```

#### 1.2 Instalar Dependências
```bash
# Instalar novas dependências
pip install -r requirements_final.txt

# OU instalar uma por uma
pip install zeep>=4.0.0
pip install cryptography>=3.0.0  
pip install click>=8.0.0
pip install tabulate>=0.9.0
pip install python-dotenv>=0.19.0
```

#### 1.3 Criar Arquivo de Configuração
```bash
# Gerar configuração de exemplo
python nfe_cli_final.py config exemplo

# Copiar e editar
cp config_exemplo.ini config.ini
nano config.ini  # Ajustar conforme suas necessidades
```

### 2. Integração com Código Existente

#### 2.1 Atualizar imports no seu projeto
No seu `auth.py` existente, certifique-se de que está funcionando com o código do `CertificateManager`:

```python
# sefaz/auth.py - Versão atualizada
# (Use o código do arquivo anexado, mas com pequenos ajustes se necessário)
```

#### 2.2 Atualizar client.py existente
Substitua ou atualize seu `client.py` com o código do `sefaz_client_completo.py`

#### 2.3 Integrar com seu config.py
Adicione as novas seções no seu `ConfigManager` existente:

```python
# No seu core/config.py existente, adicionar:
def criar_config_padrao(self):
    # ... código existente ...
    
    # Novas seções para download
    self.config['DOWNLOAD'] = {
        'max_threads': '3',
        'timeout_soap': '60',
        'intervalo_requisicoes': '1'
    }
    
    self.config['MANIFESTACAO'] = {
        'manifestar_automatico': 'false',
        'tipo_manifestacao_padrao': '210210'
    }
```

### 3. Implementação dos Webservices

#### 3.1 Endpoints SEFAZ por UF
Você precisa completar o mapeamento de endpoints no `SefazWebserviceClient`:

**Para Produção** (ambiente=1):
```python
# Adicione endpoints específicos das UFs que você atende
ENDPOINTS = {
    1: {  # Produção
        'SP': {
            'manifestacao': 'https://nfe.fazenda.sp.gov.br/ws/nfeConsManifDest.asmx?WSDL',
            'download': 'https://nfe.fazenda.sp.gov.br/ws/nfeDistDFeInteresse.asmx?WSDL'
        },
        'RJ': {
            'manifestacao': 'https://nfe.fazenda.rj.gov.br/ws/nfeConsManifDest/nfeConsManifDest.asmx?WSDL',
            'download': 'https://nfe.fazenda.rj.gov.br/ws/nfeDistDFeInteresse/nfeDistDFeInteresse.asmx?WSDL'
        },
        # Adicione outras UFs conforme necessário
    }
}
```

#### 3.2 Testar Conectividade
Primeiro teste com ambiente de homologação:

```bash
# Testar certificado
python nfe_cli_final.py test /caminho/certificado.pfx --uf RJ --ambiente 2

# Se OK, testar com produção
python nfe_cli_final.py test /caminho/certificado.pfx --uf RJ --ambiente 1
```

### 4. Configuração de Clientes

#### 4.1 Adicionar Primeiro Cliente
```bash
python nfe_cli_final.py cliente add \
  --id "cliente_teste" \
  --cnpj "12345678000195" \
  --razao-social "Empresa Teste LTDA" \
  --certificado "/caminho/para/certificado.pfx" \
  --uf "RJ" \
  --ambiente "2"
```

#### 4.2 Listar e Verificar
```bash
# Listar clientes
python nfe_cli_final.py cliente list

# Ver informações detalhadas
python nfe_cli_final.py cliente info cliente_teste
```

### 5. Primeiro Download

#### 5.1 Teste Básico
```bash
# Download de um período pequeno primeiro
python nfe_cli_final.py download nfe cliente_teste \
  --data-inicio "2025-10-01" \
  --data-fim "2025-10-13"
```

#### 5.2 Verificar Resultados
```bash
# Ver status do sistema
python nfe_cli_final.py status

# Verificar arquivos baixados
ls -la downloads_clientes/cliente_teste/nfe/
```

### 6. Integração com Processamento Existente

#### 6.1 Processar XMLs Baixados
Use seu sistema existente para processar os XMLs baixados:

```python
# Exemplo de integração
from core.processor import NFeProcessor
from core.generator import ReportGenerator

# Processar XMLs baixados
pasta_xml = "downloads_clientes/cliente_teste/nfe"
pasta_saida = "downloads_clientes/cliente_teste/relatorios"

processor = NFeProcessor(pasta_xml, pasta_saida)
processor.processar_pasta()

# Gerar relatórios
if processor.dados_processados:
    generator = ReportGenerator(processor.dados_processados)
    generator.gerar_csv("downloads_clientes/cliente_teste/relatorio.csv")
    generator.gerar_excel("downloads_clientes/cliente_teste/relatorio.xlsx")
```

#### 6.2 Script de Integração Completa
Use o `exemplo_integracao.py` para ver como combinar download + processamento:

```bash
python exemplo_integracao.py
# Escolher opção 2 (ciclo completo)
```

### 7. Automatização e Agendamento

#### 7.1 Script de Download Diário
```bash
#!/bin/bash
# download_diario.sh

# Definir datas (ontem)
DATA=$(date -d "yesterday" +%Y-%m-%d)

# Download para todos os clientes
python nfe_cli_final.py download lote \
  --data-inicio "$DATA" \
  --data-fim "$DATA" \
  --threads 3 \
  --manifestar

# Processar resultados
python exemplo_integracao.py
```

#### 7.2 Cron Job
```bash
# Adicionar ao crontab
crontab -e

# Executar todo dia às 6h da manhã
0 6 * * * /caminho/para/download_diario.sh >> /var/log/nfe_download.log 2>&1
```

### 8. Monitoramento e Manutenção

#### 8.1 Logs e Monitoramento
```bash
# Ver logs em tempo real
tail -f downloads_clientes/sistema.log

# Estatísticas do sistema
python nfe_cli_final.py status
```

#### 8.2 Limpeza Periódica
```bash
# Limpar dados antigos (90 dias)
python exemplo_integracao.py
# Escolher opção 4 (limpar dados antigos)

# Backup do banco
python exemplo_integracao.py  
# Escolher opção 5 (backup)
```

### 9. Resolução de Problemas

#### 9.1 Problemas Comuns

**Erro de Certificado:**
```bash
# Verificar se certificado existe e senha está correta
ls -la /caminho/certificado.pfx
python nfe_cli_final.py test /caminho/certificado.pfx
```

**Erro de SSL:**
```bash
# Desabilitar verificação SSL temporariamente (não recomendado para produção)
# No config.ini:
[SEFAZ]
verificar_ssl = false
```

**Erro de Timeout:**
```bash
# Aumentar timeout no config.ini:
[DOWNLOAD]
timeout_soap = 120
intervalo_requisicoes = 2
```

#### 9.2 Debug Avançado
```bash
# Modo verboso para debugging
python nfe_cli_final.py --verbose download nfe cliente_teste \
  --data-inicio "2025-10-13" \
  --data-fim "2025-10-13"
```

### 10. Expansão e Melhorias

#### 10.1 Adicionar Mais UFs
Edite o arquivo `sefaz_client_completo.py` para adicionar endpoints de outras UFs:

```python
# Adicionar no dicionário ENDPOINTS
'MG': {
    'manifestacao': 'https://nfe.fazenda.mg.gov.br/...',
    'download': 'https://nfe.fazenda.mg.gov.br/...'
}
```

#### 10.2 Implementar NFSe
Para NFSe, você precisará implementar os webservices específicos de cada município:

```python
# No futuro, implementar em nfe_download_service_final.py
def _download_nfse(self, cliente, job, pasta_cliente):
    # Implementar conforme provedor (Ginfes, ISS.NET, etc.)
    pass
```

#### 10.3 Interface Web (Futuro)
Considere criar uma interface web usando Flask ou Django para facilitar o uso:

```python
# Exemplo básico com Flask
from flask import Flask, render_template, request
from nfe_download_service_final import NFeDownloadService

app = Flask(__name__)
service = NFeDownloadService()

@app.route('/')
def dashboard():
    stats = service.obter_estatisticas_downloads()
    return render_template('dashboard.html', stats=stats)
```

### 11. Checklist de Implementação

- [ ] ✅ Ambiente preparado (pastas, dependências)
- [ ] ✅ Arquivos copiados e adaptados ao projeto
- [ ] ✅ Configuração criada e ajustada
- [ ] ✅ Certificado testado e funcionando
- [ ] ✅ Conectividade SEFAZ validada
- [ ] ✅ Primeiro cliente cadastrado
- [ ] ✅ Primeiro download realizado
- [ ] ✅ Integração com processamento existente testada
- [ ] ✅ Scripts de automação criados
- [ ] ✅ Monitoramento configurado
- [ ] ✅ Backup e limpeza implementados

### 12. Suporte e Documentação

#### 12.1 Comandos de Ajuda
```bash
# Ajuda geral
python nfe_cli_final.py --help

# Ajuda específica
python nfe_cli_final.py cliente --help
python nfe_cli_final.py download --help
```

#### 12.2 Documentação dos Webservices
- [Manual de Orientação NFe](http://www.nfe.fazenda.gov.br/portal/principal.aspx)
- [Web Services NFe](http://www.nfe.fazenda.gov.br/portal/webServices.aspx)
- [Manifestação do Destinatário](http://www.nfe.fazenda.gov.br/portal/manifestacaoDestinatario.aspx)

### 13. Exemplo Completo de Uso

```bash
# 1. Preparar ambiente
pip install -r requirements_final.txt
python nfe_cli_final.py config exemplo
cp config_exemplo.ini config.ini

# 2. Adicionar cliente
python nfe_cli_final.py cliente add \
  --id "meu_cliente" \
  --cnpj "11222333000144" \
  --razao-social "Cliente Exemplo LTDA" \
  --certificado "certificado_cliente.pfx" \
  --uf "SP" \
  --ambiente "1"

# 3. Testar conectividade
python nfe_cli_final.py test certificado_cliente.pfx --uf SP --ambiente 1

# 4. Download do mês atual
python nfe_cli_final.py download mes meu_cliente --manifestar

# 5. Ver resultados
python nfe_cli_final.py status
python nfe_cli_final.py cliente info meu_cliente

# 6. Processar XMLs baixados
python exemplo_integracao.py
# Escolher opção 2 (ciclo completo)
```

Com este guia, você tem tudo que precisa para implementar o sistema completo. Comece pelos primeiros passos e vá testando gradualmente cada funcionalidade.

Precisa de ajuda com algum passo específico?