# -*- coding: utf-8 -*-

import argparse
import os
import sys
import logging
from datetime import datetime

from cert.notifier import start_scheduler
from reforma_tributaria.config import ConfigReformaTributaria
from reforma_tributaria.calculadora import CalculadoraReformaTributaria
from reforma_tributaria.validadores import ValidadorReformaTributaria
from ia_fiscal.sugestor_tributario import SugestorTributario


# NOVO: Imports da IA Fiscal
from ia_fiscal.analisador_riscos import AnalisadorRiscos
from ia_fiscal.detector_fraudes import DetectorFraudes
from ia_fiscal.config import config_ia

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Importações do projeto
from processing.processor import NFeProcessor
from ui.gui import iniciar_gui
from ui.web import iniciar_dashboard_web
from core.config import config_manager  # <-- Importa o gestor de configuração

# NOVO: Função para inicializar IA Fiscal
def inicializar_ia_fiscal():
    """Inicializa módulos de IA Fiscal"""
    try:
        logging.info("Inicializando módulos de IA Fiscal...")
        
        analisador = AnalisadorRiscos()
        detector = DetectorFraudes()
        
        logging.info("✅ Analisador de Riscos: OK")
        logging.info("✅ Detector de Fraudes: OK") 
        logging.info("✅ Módulos de IA Fiscal inicializados com sucesso")
        
        return analisador, detector
        
    except Exception as e:
        logging.error(f"❌ Erro ao inicializar IA Fiscal: {e}")
        logging.error(f"Módulos de IA não estarão disponíveis")
        return None, None

def inicializar_reforma_tributaria():
    """Inicializa módulos da Reforma Tributária no sistema principal"""
    try:
        ano_atual = datetime.now().year
        
        # Verifica se existe configuração customizada no config.ini
        section_reforma = f"REFORMA_{ano_atual}"
        config_personalizada = False
        
        # Tenta ler configurações personalizadas (se existirem)
        try:
            # Usa o método get() com fallback ao invés de has_section()
            cbs_config = config_manager.get(section_reforma, 'cbs_ativo', fallback=None)
            if cbs_config is not None:
                config_personalizada = True
        except:
            config_personalizada = False
        
        # Se existir configuração personalizada, usa ela
        if config_personalizada:
            logging.info(f"Carregando configuração personalizada da Reforma Tributária para {ano_atual}")
            
            # Função auxiliar para converter string para boolean
            def str_to_bool(valor, padrao=False):
                if valor is None:
                    return padrao
                if isinstance(valor, bool):
                    return valor
                return str(valor).lower() in ['true', '1', 'yes', 'on', 'sim']
            
            def str_to_float(valor, padrao=0.0):
                try:
                    return float(valor) if valor is not None else padrao
                except (ValueError, TypeError):
                    return padrao
            
            # Cria configuração customizada baseada no config.ini
            config_rt = ConfigReformaTributaria(
                ano_vigencia=ano_atual,
                cbs_ativo=str_to_bool(config_manager.get(section_reforma, 'cbs_ativo', fallback='false')),
                ibs_ativo=str_to_bool(config_manager.get(section_reforma, 'ibs_ativo', fallback='false')),
                is_ativo=str_to_bool(config_manager.get(section_reforma, 'is_ativo', fallback='false')),
                aliquota_cbs=str_to_float(config_manager.get(section_reforma, 'aliquota_cbs', fallback='0.0')),
                aliquota_ibs=str_to_float(config_manager.get(section_reforma, 'aliquota_ibs', fallback='0.0')),
                pis_cofins_extinto=str_to_bool(config_manager.get(section_reforma, 'pis_cofins_extinto', fallback='false')),
                icms_iss_extinto=str_to_bool(config_manager.get(section_reforma, 'icms_iss_extinto', fallback='false'))
            )
        else:
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
        # Retorna configuração padrão em caso de erro
        config_default = ConfigReformaTributaria.get_config_por_ano(2025)
        calc_default = CalculadoraReformaTributaria(config_default)
        valid_default = ValidadorReformaTributaria(config_default)
        return config_default, calc_default, valid_default


def verificar_conformidade_sistema():
    """Verifica se o sistema está preparado para a Reforma Tributária"""
    ano_atual = datetime.now().year
    
    # Alertas baseados no cronograma oficial
    if ano_atual >= 2025:
        if ano_atual == 2025:
            logging.warning("⚠️  ATENÇÃO: Sistema deve estar preparado para Reforma Tributária até outubro/2025")
        elif ano_atual == 2026:
            logging.warning("🚨 CRÍTICO: Fase piloto CBS/IBS iniciada! Verifique configurações")
        elif ano_atual >= 2027:
            logging.warning("🔴 OBRIGATÓRIO: Reforma Tributária em vigor! Sistema deve suportar CBS/IBS/IS")

# NOVO: Função de teste da IA via CLI
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

def inicializar_ia_fiscal():
    """Inicializa módulos de IA Fiscal"""
    try:
        logging.info("Inicializando módulos de IA Fiscal...")
        
        analisador = AnalisadorRiscos()
        detector = DetectorFraudes()
        sugestor = SugestorTributario()  # NOVO
        
        logging.info("✅ Analisador de Riscos: OK")
        logging.info("✅ Detector de Fraudes: OK") 
        logging.info("✅ Sugestor Tributário: OK")  # NOVO
        logging.info("✅ Módulos de IA Fiscal inicializados com sucesso")
        
        return analisador, detector, sugestor  # NOVO
        
    except Exception as e:
        logging.error(f"❌ Erro ao inicializar IA Fiscal: {e}")
        logging.error(f"Módulos de IA não estarão disponíveis")
        return None, None, None  # NOVO
    
analisador_riscos, detector_fraudes, sugestor_tributario = inicializar_ia_fiscal()


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
    
    # NOVO: Argumentos para IA Fiscal
    parser.add_argument(
        "--teste-ia", 
        action="store_true", 
        help="Executa teste dos módulos de IA Fiscal"
    )
    parser.add_argument(
        "--analise-risco",
        type=str,
        help="Analisa risco de uma pasta de XMLs específica"
    )

    args = parser.parse_args()

    # Inicializa Reforma Tributária
    config_rt, calc_rt, valid_rt = inicializar_reforma_tributaria()
    
    # NOVO: Inicializa IA Fiscal
    analisador_riscos, detector_fraudes = inicializar_ia_fiscal()

    # Torna as instâncias globalmente disponíveis para outros módulos
    import __main__
    __main__.reforma_config = config_rt
    __main__.reforma_calculadora = calc_rt
    __main__.reforma_validador = valid_rt
    
    # NOVO: Disponibiliza IA globalmente
    __main__.ia_analisador = analisador_riscos
    __main__.ia_detector = detector_fraudes

    # NOVO: Comando específico para teste da IA
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
    
    # NOVO: Comando para análise de risco de pasta
    if args.analise_risco:
        if analisador_riscos:
            executar_analise_risco_pasta(args.analise_risco, analisador_riscos, detector_fraudes)
        else:
            logging.error("IA Fiscal não disponível para análise de risco")
        return

    # Usa os caminhos do config.ini como padrão
    pasta_xml_final = args.pasta_xml or config_manager.get('PADRAO', 'pasta_xml')
    pasta_saida_final = args.saida or config_manager.get('PADRAO', 'pasta_saida')

    # Se nenhum argumento for passado ou --gui for usado, abre a interface gráfica
    if len(sys.argv) == 1 or args.gui:
        logging.info("Iniciando interface gráfica com suporte à IA Fiscal e Reforma Tributária")
        iniciar_gui()

    # Se --web for usado
    elif args.web:
        if not pasta_xml_final or not os.path.isdir(pasta_xml_final):
            logging.error("A pasta de XMLs não foi especificada ou não é válida. Use --gui para selecionar ou edite o config.ini.")
            return

        logging.info("Iniciando dashboard web com IA Fiscal e análise da Reforma Tributária")
        processor_web = NFeProcessor(pasta_xml_final, pasta_saida_final)
        # Injeta configurações no processor
        processor_web.reforma_config = config_rt
        processor_web.reforma_calculadora = calc_rt
        processor_web.ia_analisador = analisador_riscos
        processor_web.ia_detector = detector_fraudes
        iniciar_dashboard_web(processor_web)

    # Se um caminho para a pasta de XMLs for fornecido
    elif pasta_xml_final:
        if not os.path.isdir(pasta_xml_final):
            logging.error(f"O caminho especificado para os XMLs não existe ou não é uma pasta: {pasta_xml_final}")
            return

        # Salva os caminhos usados no config para a próxima vez
        config_manager.set('PADRAO', 'pasta_xml', pasta_xml_final)
        config_manager.set('PADRAO', 'pasta_saida', pasta_saida_final)
        config_manager.save()

        logging.info("Processando NFe com IA Fiscal e análise da Reforma Tributária")
        processor_cli = NFeProcessor(pasta_xml_final, pasta_saida_final)
        # Injeta configurações no processor
        processor_cli.reforma_config = config_rt
        processor_cli.reforma_calculadora = calc_rt
        processor_cli.ia_analisador = analisador_riscos  
        processor_cli.ia_detector = detector_fraudes
        processor_cli.processar_pasta()
        processor_cli.calcular_resumos()
        processor_cli.gerar_relatorios()

    # Se nenhum dos casos acima for atendido, mostra a ajuda
    else:
        parser.print_help()
        logging.info("\nNenhum caminho especificado. Use --gui para abrir a interface gráfica.")

# NOVO: Função para análise de risco de pasta inteira
def executar_analise_risco_pasta(pasta_xml, analisador, detector):
    """Analisa riscos de todos os XMLs em uma pasta"""
    print(f"=== ANÁLISE DE RISCO - PASTA: {pasta_xml} ===\n")
    
    if not os.path.isdir(pasta_xml):
        print(f"❌ Pasta não encontrada: {pasta_xml}")
        return
    
    xml_files = [f for f in os.listdir(pasta_xml) if f.endswith('.xml')]
    if not xml_files:
        print("❌ Nenhum arquivo XML encontrado na pasta")
        return
    
    print(f"Analisando {len(xml_files)} arquivo(s) XML...\n")
    
    riscos_altos = 0
    riscos_medios = 0
    inconsistencias_total = 0
    
    for xml_file in xml_files[:5]:  # Analisa apenas os primeiros 5 para demo
        print(f"📄 {xml_file}:")
        
        # Aqui você implementaria a leitura do XML
        # Por agora, simulamos dados
        nfe_dados = {
            'cnpj_emissor': '11222333000181',
            'valor_total': 1500.00,
            'data_emissao': '2025-09-12'
        }
        
        # Análise de risco
        risco = analisador.analisar_nfe(nfe_dados)
        print(f"   🎯 Risco: {risco.nivel.upper()} ({risco.score:.2f})")
        
        if risco.nivel in ['alto', 'critico']:
            riscos_altos += 1
        elif risco.nivel == 'medio':
            riscos_medios += 1
        
        # Detecção de inconsistências
        inconsistencias = detector.detectar_inconsistencias(nfe_dados)
        if inconsistencias:
            print(f"   ⚠️  {len(inconsistencias)} inconsistência(s)")
            inconsistencias_total += len(inconsistencias)
        else:
            print("   ✅ Sem inconsistências")
        
        print()
    
    # Resumo final
    print("=== RESUMO DA ANÁLISE ===")
    print(f"Arquivos analisados: {min(len(xml_files), 5)}")
    print(f"Riscos altos/críticos: {riscos_altos}")
    print(f"Riscos médios: {riscos_medios}")
    print(f"Total de inconsistências: {inconsistencias_total}")
    print(f"Recomendação: {'Revisar arquivos com risco alto' if riscos_altos > 0 else 'Processamento pode prosseguir'}")

def executar_teste_reforma(config_rt, calc_rt, valid_rt):
    """Executa teste dos módulos da Reforma Tributária via linha de comando"""
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
    print(f"  ICMS/ISS:   {'🔴 Extinto' if config_rt.icms_iss_extinto else '🔴 Ativo'}")
    
    # Cronograma
    print(f"\nCronograma da Reforma:")
    print(f"  2025: Preparação {'✅' if ano_atual >= 2025 else '⏳'}")
    print(f"  2026: Fase Piloto CBS/IBS {'✅' if ano_atual >= 2026 else '⏳'}")
    print(f"  2027: CBS Integral {'✅' if ano_atual >= 2027 else '⏳'}")
    print(f"  2033: Sistema Completo {'✅' if ano_atual >= 2033 else '⏳'}")

if __name__ == "__main__":
    # Inicia o agendador de certificados antes de qualquer outra coisa
    try:
        start_scheduler()
        logging.info("✅ Agendador de certificados digitais iniciado")
    except Exception as e:
        logging.error(f"❌ Erro ao iniciar agendador de certificados: {e}")
    
    # Em seguida, chama a função principal do programa
    main()