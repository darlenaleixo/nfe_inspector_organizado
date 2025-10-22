# teste_integracao_completa.py

from processing.processor import NFeProcessorBI
from database.models import DatabaseManager
import logging

def testar_integracao_completa():
    """Teste completo: XML → IA → Banco → Dashboard"""
    
    logging.basicConfig(level=logging.INFO)
    print("=== TESTE INTEGRAÇÃO COMPLETA ===\n")
    
    # 1. Processar XMLs com BI
    pasta_xml = "caminho/para/seus/xmls"  # Substitua pelo seu caminho
    pasta_saida = "caminho/relatorios"
    
    print("1. Processando XMLs com IA e salvando no banco...")
    processor = NFeProcessorBI(pasta_xml, pasta_saida)
    estatisticas = processor.processar_pasta()
    
    print(f"✅ Processamento concluído:")
    for chave, valor in estatisticas.items():
        print(f"   {chave}: {valor}")
    
    # 2. Testar consultas no banco
    print("\n2. Testando consultas no banco...")
    db_manager = processor.obter_dashboard_manager()
    
    # Estatísticas gerais
    stats = db_manager.obter_estatisticas()
    print(f"   Total de NFe no banco: {stats.get('total_notas', 0)}")
    print(f"   Valor total: R$ {stats.get('valor_total', 0):,.2f}")
    
    # Empresas cadastradas
    empresas = db_manager.listar_empresas()
    print(f"   Empresas cadastradas: {len(empresas)}")
    
    # 3. Testar filtros
    print("\n3. Testando filtros...")
    from datetime import datetime, timedelta
    
    filtros = {
        'data_inicio': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'data_fim': datetime.now().strftime('%Y-%m-%d')
    }
    
    notas = db_manager.consultar_notas_fiscais(filtros)
    print(f"   NFe dos últimos 30 dias: {len(notas)}")
    
    print("\n🎯 Integração funcionando! Use: python main.py --dashboard")

if __name__ == "__main__":
    testar_integracao_completa()
