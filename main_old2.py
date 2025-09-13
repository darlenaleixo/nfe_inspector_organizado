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
from ia_fiscal.analisador_riscos import AnalisadorRiscos
from ia_fiscal.detector_fraudes import DetectorFraudes

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

def inicializar_reforma_tributaria():
    """Inicializa módulos da Reforma Tributária no sistema principal"""
    try:
        ano_atual = datetime.now().year
        
        # Verifica se existe configuração customizada no config.ini
        section_reforma = f"REFORMA_{ano_atual}"
        
        # Se existir configuração personalizada, usa ela
        if config_manager.has_section(section_reforma):
            logging.info(f"Carregando configuração personalizada da Reforma Tributária para {ano_atual}")
            
            # Cria configuração customizada baseada no config.ini
            config_rt = ConfigReformaTributaria(
                ano_vigencia=ano_atual,
                cbs_ativo=config_manager.getboolean(section_reforma, 'cbs_ativo', fallback=False),
                ibs_ativo=config_manager.getboolean(section_reforma, 'ibs_ativo', fallback=False),
                is_ativo=config_manager.getboolean(section_reforma, 'is_ativo', fallback=False),
                aliquota_cbs=config_manager.getfloat(section_reforma, 'aliquota_cbs', fallback=0.0),
                aliquota_ibs=config_manager.getfloat(section_reforma, 'aliquota_ibs', fallback=0.0),
                pis_cofins_extinto=config_manager.getboolean(section_reforma, 'pis_cofins_extinto', fallback=False),
                icms_iss_extinto=config_manager.getboolean(section_reforma, 'icms_iss_extinto', fallback=False)
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

def main():
    """Função principal que gerencia a execução do programa via CLI ou GUI."""
    
    # Verifica conformidade antes de iniciar
    verificar_conformidade_sistema()
    
    parser = argparse.ArgumentParser(
        description="Analisador de Notas Fiscais Eletrônicas (NFe/NFCe) com suporte à Reforma Tributária",
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
    
    # Novos argumentos para Reforma Tributária
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

    args = parser.parse_args()

    # Inicializa Reforma Tributária
    config_rt, calc_rt, valid_rt = inicializar_reforma_tributaria()

    # Torna as instâncias globalmente disponíveis para outros módulos
    import __main__
    __main__.reforma_config = config_rt
    __main__.reforma_calculadora = calc_rt
    __main__.reforma_validador = valid_rt

    # Comando específico para teste da reforma
    if args.teste_reforma:
        executar_teste_reforma(config_rt, calc_rt, valid_rt)
        return

    # Comando para status da reforma
    if args.status_reforma:
        exibir_status_reforma(config_rt)
        return

    # Usa os caminhos do config.ini como padrão
    pasta_xml_final = args.pasta_xml or config_manager.get('PADRAO', 'pasta_xml')
    pasta_saida_final = args.saida or config_manager.get('PADRAO', 'pasta_saida')

    # Se nenhum argumento for passado ou --gui for usado, abre a interface gráfica
    if len(sys.argv) == 1 or args.gui:
        logging.info("Iniciando interface gráfica com suporte à Reforma Tributária")
        iniciar_gui()

    # Se --web for usado
    elif args.web:
        if not pasta_xml_final or not os.path.isdir(pasta_xml_final):
            logging.error("A pasta de XMLs não foi especificada ou não é válida. Use --gui para selecionar ou edite o config.ini.")
            return

        logging.info("Iniciando dashboard web com análise da Reforma Tributária")
        processor_web = NFeProcessor(pasta_xml_final, pasta_saida_final)
        # Injeta configuração da reforma no processor
        processor_web.reforma_config = config_rt
        processor_web.reforma_calculadora = calc_rt
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

        logging.info("Processando NFe com análise da Reforma Tributária")
        processor_cli = NFeProcessor(pasta_xml_final, pasta_saida_final)
        # Injeta configuração da reforma no processor
        processor_cli.reforma_config = config_rt
        processor_cli.reforma_calculadora = calc_rt
        processor_cli.processar_pasta()
        processor_cli.calcular_resumos()
        processor_cli.gerar_relatorios()

    # Se nenhum dos casos acima for atendido, mostra a ajuda
    else:
        parser.print_help()
        logging.info("\nNenhum caminho especificado. Use --gui para abrir a interface gráfica.")

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
    print(f"  ICMS/ISS:   {'🔴 Extinto' if config_rt.icms_iss_extinto else '🟢 Ativo'}")
    
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