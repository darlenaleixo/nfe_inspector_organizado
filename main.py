# -*- coding: utf-8 -*-

import argparse
import os
import sys
import logging
import tkinter as tk
from datetime import datetime

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# === IMPORTS SEGUROS COM TRATAMENTO DE ERRO ===

# Imports básicos
from core.config import config_manager

# Certificados
try:
    from cert.notifier import start_scheduler
except ImportError as e:
    logging.warning(f"Módulo de certificados não disponível: {e}")
    start_scheduler = None

# Reforma Tributária
try:
    from reforma_tributaria.config import ConfigReformaTributaria
    from reforma_tributaria.calculadora import CalculadoraReformaTributaria
    from reforma_tributaria.validadores import ValidadorReformaTributaria
except ImportError as e:
    logging.warning(f"Módulos da Reforma Tributária não disponíveis: {e}")
    ConfigReformaTributaria = None
    CalculadoraReformaTributaria = None
    ValidadorReformaTributaria = None

# IA Fiscal
try:
    from ia_fiscal.analisador_riscos import AnalisadorRiscos
    from ia_fiscal.detector_fraudes import DetectorFraudes
    from ia_fiscal.sugestor_tributario import SugestorTributario
except ImportError as e:
    logging.warning(f"Módulos de IA Fiscal não disponíveis: {e}")
    AnalisadorRiscos = None
    DetectorFraudes = None
    SugestorTributario = None

# Processamento
try:
    from processing.processor import NFeProcessorBI
except ImportError:
    try:
        from processing.processor import NFeProcessor as NFeProcessorBI
    except ImportError as e:
        logging.warning(f"Módulo de processamento não disponível: {e}")
        NFeProcessorBI = None

# Database
try:
    from database.models import DatabaseManager
except ImportError as e:
    logging.warning(f"Módulo de banco de dados não disponível: {e}")
    DatabaseManager = None

# Interfaces
try:
    from ui.gui import iniciar_gui
except ImportError as e:
    logging.error(f"Interface GUI não disponível: {e}")
    iniciar_gui = None

try:
    from ui.web import iniciar_dashboard_web
except ImportError as e:
    logging.warning(f"Dashboard web não disponível: {e}")
    iniciar_dashboard_web = None

# === FUNÇÕES DE INICIALIZAÇÃO ===

def inicializar_reforma_tributaria():
    """Inicializa módulos da Reforma Tributária"""
    if not ConfigReformaTributaria:
        logging.warning("⚠️ Reforma Tributária não disponível")
        return None, None, None
    
    try:
        ano_atual = datetime.now().year
        
        # Usa configuração padrão baseada no ano
        config_rt = ConfigReformaTributaria.get_config_por_ano(ano_atual)
        logging.info(f"Usando configuração padrão da Reforma Tributária para {ano_atual}")
        
        # Inicializa calculadora e validador
        calculadora = CalculadoraReformaTributaria(config_rt)
        validador = ValidadorReformaTributaria(config_rt)
        
        # Log do status da reforma
        if config_rt.cbs_ativo or config_rt.ibs_ativo:
            logging.info("=== REFORMA TRIBUTÁRIA ATIVA ===")
            if config_rt.cbs_ativo:
                logging.info(f"CBS: {config_rt.aliquota_cbs:.3%} (ativo)")
            if config_rt.ibs_ativo:
                logging.info(f"IBS: {config_rt.aliquota_ibs:.3%} (ativo)")
            if config_rt.is_ativo:
                logging.info("IS: Imposto Seletivo (ativo)")
            logging.info("==================================")
        else:
            logging.info("Reforma Tributária: Modo preparação (CBS/IBS inativos)")
        
        return config_rt, calculadora, validador
        
    except Exception as e:
        logging.error(f"Erro ao inicializar Reforma Tributária: {e}")
        return None, None, None

def inicializar_ia_fiscal():
    """Inicializa módulos de IA Fiscal"""
    if not AnalisadorRiscos or not DetectorFraudes:
        logging.warning("⚠️ IA Fiscal não disponível")
        return None, None, None
    
    try:
        logging.info("Inicializando módulos de IA Fiscal...")
        
        analisador = AnalisadorRiscos()
        detector = DetectorFraudes()
        sugestor = SugestorTributario() if SugestorTributario else None
        
        logging.info("✅ Analisador de Riscos: OK")
        logging.info("✅ Detector de Fraudes: OK")
        if sugestor:
            logging.info("✅ Sugestor Tributário: OK")
        logging.info("✅ Módulos de IA Fiscal inicializados com sucesso")
        
        return analisador, detector, sugestor
        
    except Exception as e:
        logging.error(f"❌ Erro ao inicializar IA Fiscal: {e}")
        return None, None, None

def verificar_conformidade_sistema():
    """Verifica se o sistema está preparado para a Reforma Tributária"""
    ano_atual = datetime.now().year
    
    # Alertas baseados no cronograma oficial
    if ano_atual >= 2025:
        if ano_atual == 2025:
            logging.warning("⚠️ ATENÇÃO: Sistema deve estar preparado para Reforma Tributária até outubro/2025")
        elif ano_atual == 2026:
            logging.warning("🚨 CRÍTICO: Fase piloto CBS/IBS iniciada! Verifique configurações")
        elif ano_atual >= 2027:
            logging.warning("🔴 OBRIGATÓRIO: Reforma Tributária em vigor! Sistema deve suportar CBS/IBS/IS")

# === FUNÇÕES DE TESTE ===

def executar_teste_ia_fiscal(analisador, detector):
    """Executa teste dos módulos de IA Fiscal via linha de comando"""
    if not analisador or not detector:
        print("❌ Módulos de IA Fiscal não disponíveis")
        return
        
    print("=== TESTE IA FISCAL (CLI) ===\n")
    
    # Dados de exemplo de uma NFe
    nfe_teste = {
        'cnpj_emissor': '11222333000181',
        'documento_destinatario': '98765432000119',
        'tipo_documento_destinatario': 'cnpj',
        'valor_total': 50000.00,
        'valor_produtos': 45000.00,
        'valor_impostos': 5000.00,
        'data_emissao': '2025-09-12',
        'cfop': '5101',
        'uf_emissor': 'SP',
        'uf_destinatario': 'RJ',
        'itens': [{
            'ncm': '12345678',
            'quantidade': 10,
            'icms_cst': '00',
            'icms_aliquota': 0.18
        }]
    }
    
    # Teste do Analisador de Riscos
    print("1. ANÁLISE DE RISCOS:")
    risco = analisador.analisar_nfe(nfe_teste)
    
    print(f"   Score de Risco: {risco.score:.2f}")
    print(f"   Nível: {risco.nivel.upper()}")
    print(f"   Confiança: {risco.confianca:.2f}")
    
    if risco.fatores:
        print("   Fatores de Risco:")
        for fator in risco.fatores:
            print(f"   - {fator}")
    
    if risco.recomendacoes:
        print("   Recomendações:")
        for rec in risco.recomendacoes:
            print(f"   - {rec}")
    
    print()
    
    # Teste do Detector de Fraudes
    print("2. DETECÇÃO DE INCONSISTÊNCIAS:")
    inconsistencias = detector.detectar_inconsistencias(nfe_teste)
    
    if inconsistencias:
        print(f"   {len(inconsistencias)} inconsistência(s) encontrada(s):")
        for inc in inconsistencias:
            print(f"   - {inc['severidade'].upper()}: {inc['descricao']}")
    else:
        print("   ✅ Nenhuma inconsistência detectada")
    
    print("\n✅ Teste de IA Fiscal concluído!")

def executar_teste_reforma(config_rt, calc_rt, valid_rt):
    """Executa teste dos módulos da Reforma Tributária via linha de comando"""
    if not config_rt or not calc_rt:
        print("❌ Módulos da Reforma Tributária não disponíveis")
        return
        
    print("=== TESTE REFORMA TRIBUTÁRIA (CLI) ===\n")
    
    # Teste configuração
    print(f"Configuração atual ({config_rt.ano_vigencia}):")
    print(f"  CBS: {'Ativo' if config_rt.cbs_ativo else 'Inativo'} ({config_rt.aliquota_cbs:.3%})")
    print(f"  IBS: {'Ativo' if config_rt.ibs_ativo else 'Inativo'} ({config_rt.aliquota_ibs:.3%})")
    print(f"  IS:  {'Ativo' if config_rt.is_ativo else 'Inativo'}\n")
    
    # Teste cálculos
    if config_rt.cbs_ativo or config_rt.ibs_ativo:
        print("Teste de cálculo em produto R$ 1.000,00:")
        cbs = calc_rt.calcular_cbs(1000.0, {})
        ibs = calc_rt.calcular_ibs(1000.0, {})
        print(f"  CBS: R$ {cbs['valor']:.2f}")
        print(f"  IBS: R$ {ibs['valor']:.2f}")
        
        if config_rt.ano_vigencia == 2026:
            comp = calc_rt.calcular_credito_compensacao(cbs['valor'], ibs['valor'])
            print(f"  Compensação PIS/COFINS: R$ {comp['total_compensavel']:.2f}")
    
    print("\n✅ Teste concluído!")

def exibir_status_reforma(config_rt):
    """Exibe status detalhado da Reforma Tributária"""
    if not config_rt:
        print("❌ Reforma Tributária não disponível")
        return
        
    print("=== STATUS REFORMA TRIBUTÁRIA ===\n")
    
    ano_atual = datetime.now().year
    print(f"Ano atual: {ano_atual}")
    print(f"Configuração ativa: {config_rt.ano_vigencia}")
    
    print(f"\nTributos:")
    print(f"  CBS: {'🟢 Ativo' if config_rt.cbs_ativo else '🔴 Inativo'} ({config_rt.aliquota_cbs:.3%})")
    print(f"  IBS: {'🟢 Ativo' if config_rt.ibs_ativo else '🔴 Inativo'} ({config_rt.aliquota_ibs:.3%})")
    print(f"  IS:  {'🟢 Ativo' if config_rt.is_ativo else '🔴 Inativo'}")
    
    print(f"\nTributos extintos:")
    print(f"  PIS/COFINS: {'🔴 Extinto' if config_rt.pis_cofins_extinto else '🟢 Ativo'}")
    print(f"  ICMS/ISS:   {'🔴 Extinto' if config_rt.icms_iss_extinto else '🟢 Ativo'}")
    
    # Cronograma
    print(f"\nCronograma da Reforma:")
    print(f"  2025: Preparação {'✅' if ano_atual >= 2025 else '⏳'}")
    print(f"  2026: Fase Piloto CBS/IBS {'✅' if ano_atual >= 2026 else '⏳'}")
    print(f"  2027: CBS Integral {'✅' if ano_atual >= 2027 else '⏳'}")
    print(f"  2033: Sistema Completo {'✅' if ano_atual >= 2033 else '⏳'}")

# === FUNÇÃO PRINCIPAL ===

def main():
    """Função principal que gerencia a execução do programa via CLI ou GUI."""
    
    # Verifica conformidade antes de iniciar
    verificar_conformidade_sistema()
    
    parser = argparse.ArgumentParser(
        description="Analisador de Notas Fiscais Eletrônicas (NFe/NFCe) com IA e Reforma Tributária",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "pasta_xml",
        type=str,
        nargs="?",
        default=None,
        help="Caminho para a pasta contendo os arquivos XML de NFe/NFCe."
    )

    parser.add_argument(
        "--saida",
        type=str,
        default=None,
        help="Caminho para a pasta onde os relatórios serão salvos."
    )

    parser.add_argument("--gui", action="store_true", help="Inicia a interface gráfica (GUI).")
    parser.add_argument("--web", action="store_true", help="Inicia o dashboard web interativo.")
    parser.add_argument("--dashboard", action="store_true", help="Inicia o Dashboard Business Intelligence.")
    
    # Argumentos para Reforma Tributária
    parser.add_argument(
        "--teste-reforma", 
        action="store_true", 
        help="Executa teste dos módulos da Reforma Tributária"
    )
    parser.add_argument(
        "--status-reforma", 
        action="store_true", 
        help="Exibe status atual da configuração da Reforma Tributária"
    )
    
    # Argumentos para IA Fiscal
    parser.add_argument(
        "--teste-ia", 
        action="store_true", 
        help="Executa teste dos módulos de IA Fiscal"
    )

    args = parser.parse_args()

    # === INICIALIZAÇÕES ===
    
    # Inicializa Reforma Tributária
    config_rt, calc_rt, valid_rt = inicializar_reforma_tributaria()
    
    # Inicializa IA Fiscal
    analisador_riscos, detector_fraudes, sugestor_tributario = inicializar_ia_fiscal()

    # Torna as instâncias globalmente disponíveis para outros módulos
    import __main__
    __main__.reforma_config = config_rt
    __main__.reforma_calculadora = calc_rt
    __main__.reforma_validador = valid_rt
    __main__.ia_analisador = analisador_riscos
    __main__.ia_detector = detector_fraudes
    __main__.ia_sugestor = sugestor_tributario

    # === COMANDOS ESPECÍFICOS ===

    # Comando específico para teste da IA
    if args.teste_ia:
        executar_teste_ia_fiscal(analisador_riscos, detector_fraudes)
        return

    # Comando específico para teste da reforma
    if args.teste_reforma:
        executar_teste_reforma(config_rt, calc_rt, valid_rt)
        return

    # Comando para status da reforma
    if args.status_reforma:
        exibir_status_reforma(config_rt)
        return
    
    # === DASHBOARD BUSINESS INTELLIGENCE ===
    if args.dashboard:
        if not DatabaseManager:
            print("❌ Módulo de banco de dados não disponível para Dashboard BI")
            return
            
        try:
            from ui.dashboard_nfe import DashboardNFe
            
            print("🚀 Iniciando Dashboard Business Intelligence...")
            db_manager = DatabaseManager()
            
            # Cria janela principal
            root = tk.Tk()
            root.withdraw()  # Oculta janela principal
            
            # Abre Dashboard BI
            dashboard = DashboardNFe(root, db_manager)
            root.mainloop()
            return
            
        except ImportError as e:
            print(f"❌ Dashboard BI não disponível: {e}")
            return
        except Exception as e:
            print(f"❌ Erro ao abrir Dashboard BI: {e}")
            return

    # === INTERFACES PRINCIPAIS ===

    # Usa os caminhos do config.ini como padrão
    pasta_xml_final = args.pasta_xml or config_manager.get('PADRAO', 'pasta_xml')
    pasta_saida_final = args.saida or config_manager.get('PADRAO', 'pasta_saida')

    # Se nenhum argumento for passado ou --gui for usado, abre a interface gráfica
    if len(sys.argv) == 1 or args.gui:
        if not iniciar_gui:
            print("❌ Interface GUI não disponível")
            return
            
        logging.info("Iniciando interface gráfica com suporte à IA Fiscal e Reforma Tributária")
        try:
            iniciar_gui()
        except Exception as e:
            print(f"❌ Erro ao iniciar GUI: {e}")
            logging.error(f"Erro na GUI: {e}")

    # Se --web for usado
    elif args.web:
        if not iniciar_dashboard_web:
            print("❌ Dashboard web não disponível")
            return
            
        if not pasta_xml_final or not os.path.isdir(pasta_xml_final):
            logging.error("A pasta de XMLs não foi especificada ou não é válida. Use --gui para selecionar ou edite o config.ini.")
            return

        logging.info("Iniciando dashboard web com IA Fiscal e análise da Reforma Tributária")
        
        if NFeProcessorBI:
            processor_web = NFeProcessorBI(pasta_xml_final, pasta_saida_final)
        else:
            print("❌ Processador de NFe não disponível")
            return
            
        # Injeta configurações no processor
        if config_rt:
            processor_web.reforma_config = config_rt
            processor_web.reforma_calculadora = calc_rt
        if analisador_riscos:
            processor_web.ia_analisador = analisador_riscos
            processor_web.ia_detector = detector_fraudes
            
        iniciar_dashboard_web(processor_web)

    # Se um caminho para a pasta de XMLs for fornecido
    elif pasta_xml_final:
        if not NFeProcessorBI:
            print("❌ Processador de NFe não disponível")
            return
            
        if not os.path.isdir(pasta_xml_final):
            logging.error(f"O caminho especificado para os XMLs não existe ou não é uma pasta: {pasta_xml_final}")
            return

        # Salva os caminhos usados no config para a próxima vez
        config_manager.set('PADRAO', 'pasta_xml', pasta_xml_final)
        config_manager.set('PADRAO', 'pasta_saida', pasta_saida_final)
        config_manager.save()

        logging.info("Processando NFe com IA Fiscal e análise da Reforma Tributária")
        
        processor_cli = NFeProcessorBI(pasta_xml_final, pasta_saida_final)
        
        # Injeta configurações no processor
        if config_rt:
            processor_cli.reforma_config = config_rt
            processor_cli.reforma_calculadora = calc_rt
        if analisador_riscos:
            processor_cli.ia_analisador = analisador_riscos  
            processor_cli.ia_detector = detector_fraudes
            
        try:
            estatisticas = processor_cli.processar_pasta()
            
            # Chama métodos de compatibilidade
            processor_cli.calcular_resumos()
            processor_cli.gerar_relatorios()
            
            print("\n=== PROCESSAMENTO CONCLUÍDO ===")
            for chave, valor in estatisticas.items():
                print(f"{chave.replace('_', ' ').title()}: {valor}")
            print("✅ Processamento finalizado com sucesso!")
            
        except Exception as e:
            logging.error(f"Erro no processamento: {e}")
            print(f"❌ Erro no processamento: {e}")
            
# === ENTRADA PRINCIPAL ===

if __name__ == "__main__":
    # Inicia o agendador de certificados antes de qualquer outra coisa
    if start_scheduler:
        try:
            start_scheduler()
            logging.info("✅ Agendador de certificados digitais iniciado")
        except Exception as e:
            logging.error(f"❌ Erro ao iniciar agendador de certificados: {e}")
    
    # Em seguida, chama a função principal do programa
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Programa interrompido pelo usuário")
    except Exception as e:
        logging.error(f"❌ Erro crítico: {e}")
        print(f"❌ Erro crítico: {e}")
