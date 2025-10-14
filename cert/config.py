# -*- coding: utf-8 -*-
import os
import configparser
from pathlib import Path

CONFIG_FILE_NAME = "config.ini"


class ConfigManager:
    """
    Gerencia o ficheiro de configuração (config.ini) para a aplicação.
    """
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_file):
            self._create_default_config()
        self.config.read(self.config_file, encoding='utf-8')

    def _create_default_config(self):
        """Cria uma estrutura de configuração padrão."""
        self.config['PADRAO'] = {
            'pasta_xml': '',
            'pasta_saida': os.path.join(os.getcwd(), 'relatorios_nfe')
        }
        self.config['SEFAZ'] = {
            'caminho_certificado_a1': '',
            'uf': 'RJ',
            'ambiente': '1',
            'verificar_ssl': 'true' # <-- NOVA OPÇÃO
        }
        self.save()

    def get(self, section, key, fallback=''):
        """Obtém um valor do ficheiro de configuração."""
        return self.config.get(section, key, fallback=fallback)

    def getboolean(self, section, key, fallback=False):
        """Obtém um valor booleano do ficheiro de configuração."""
        return self.config.getboolean(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Define um valor no ficheiro de configuração."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save(self):
        """Salva as configurações atuais no ficheiro .ini."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

# Instância única para ser usada em todo o projeto
config_manager = ConfigManager()

