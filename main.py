# -*- coding: utf-8 -*-
import argparse
import os
import sys
import logging

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
from core.config import config_manager # <-- Importa o gestor de configuração

def main():
    """Função principal que gerencia a execução do programa via CLI ou GUI."""
    parser = argparse.ArgumentParser(
        description="Analisador de Notas Fiscais Eletrônicas (NFe/NFCe)",
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
    
    args = parser.parse_args()

    # Usa os caminhos do config.ini como padrão
    pasta_xml_final = args.pasta_xml or config_manager.get('PADRAO', 'pasta_xml')
    pasta_saida_final = args.saida or config_manager.get('PADRAO', 'pasta_saida')

    # Se nenhum argumento for passado ou --gui for usado, abre a interface gráfica
    if len(sys.argv) == 1 or args.gui:
        iniciar_gui()
    
    # Se --web for usado
    elif args.web:
        if not pasta_xml_final or not os.path.isdir(pasta_xml_final):
            logging.error("A pasta de XMLs não foi especificada ou não é válida. Use --gui para selecionar ou edite o config.ini.")
            return
        processor_web = NFeProcessor(pasta_xml_final, pasta_saida_final)
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

        processor_cli = NFeProcessor(pasta_xml_final, pasta_saida_final)
        processor_cli.processar_pasta()
        processor_cli.calcular_resumos()
        processor_cli.gerar_relatorios()
        
    # Se nenhum dos casos acima for atendido, mostra a ajuda
    else:
        parser.print_help()
        logging.info("\nNenhum caminho especificado. Use --gui para abrir a interface gráfica.")

if __name__ == "__main__":
    main()

