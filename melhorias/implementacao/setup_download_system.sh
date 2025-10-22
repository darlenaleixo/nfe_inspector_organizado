#!/bin/bash
# Script de implementação automática do sistema de download

echo "🚀 Implementando Sistema de Download NFe/NFSe"
echo "=============================================="

# Verificar se estamos no diretório correto
if [ ! -f "parser.py" ] && [ ! -d "core" ]; then
    echo "❌ Execute este script no diretório do projeto nfe_inspector_organizado"
    exit 1
fi

echo "📁 Criando estrutura de pastas..."
mkdir -p download sefaz schemas
touch download/__init__.py sefaz/__init__.py

echo "📦 Instalando dependências..."
pip install zeep cryptography click tabulate python-dotenv

echo "⚙️ Criando configuração padrão..."
cat > config.ini << 'EOF'
[PADRAO]
pasta_xml = 
pasta_saida = downloads_clientes

[SEFAZ]
caminho_certificado_a1 = 
uf = RJ
ambiente = 2
verificar_ssl = true

[DOWNLOAD]
max_threads = 3
timeout_soap = 60
intervalo_requisicoes = 1
max_tentativas = 3

[MANIFESTACAO]
manifestar_automatico = false
tipo_manifestacao_padrao = 210210

[LOGGING]
nivel = INFO
arquivo_log = 

[BANCO]
caminho_db = clientes.db
backup_automatico = true
max_backups = 5
EOF

echo "✅ Configuração criada em config.ini"

echo "📄 Criando arquivo de exemplo para testar..."
cat > exemplo_teste.py << 'EOF'
#!/usr/bin/env python3
"""
Script de exemplo para testar o sistema após implementação
"""

import sys
from pathlib import Path

# Adicionar ao path se necessário
sys.path.append(str(Path(__file__).parent))

try:
    from download.service import NFeDownloadService, Cliente
    from sefaz.webservice_client import SefazWebserviceClient
    from sefaz.auth import CertificateManager
    print("✅ Imports OK - sistema implementado corretamente!")
    
    # Testar inicialização básica
    service = NFeDownloadService()
    print("✅ Serviço inicializado - banco de dados criado")
    
    # Mostrar clientes cadastrados
    clientes = service.cliente_manager.listar_clientes()
    print(f"📋 Clientes cadastrados: {len(clientes)}")
    
    if clientes:
        for c in clientes:
            print(f"   - {c.id}: {c.razao_social} ({c.uf})")
    
    print("\n🎉 Sistema pronto para uso!")
    print("💡 Próximos passos:")
    print("   1. python nfe_cli.py cliente add (para adicionar cliente)")
    print("   2. python nfe_cli.py test certificado.pfx (para testar)")
    print("   3. python nfe_cli.py download nfe cliente_id --data-inicio ... --data-fim ...")

except ImportError as e:
    print(f"❌ Erro de import: {e}")
    print("💡 Verifique se todos os arquivos foram copiados corretamente")
except Exception as e:
    print(f"⚠️ Erro: {e}")
    print("💡 Verifique a implementação")
EOF

chmod +x exemplo_teste.py

echo "🎯 Script de setup concluído!"
echo ""
echo "📝 Próximos passos:"
echo "1. Copie os arquivos principais (códigos dos attachments)"
echo "2. Ajuste os imports conforme indicado"  
echo "3. Execute: python exemplo_teste.py"
echo "4. Se OK, execute: python nfe_cli.py --help"
echo ""
echo "📚 Arquivos que você precisa copiar:"
echo "   - sefaz_client_completo.py → sefaz/webservice_client.py"
echo "   - nfe_download_service_final.py → download/service.py" 
echo "   - nfe_cli_final.py → nfe_cli.py"
echo ""
echo "✨ Após copiar, execute 'python exemplo_teste.py' para validar"