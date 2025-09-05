# -*- coding: utf-8 -*-
import configparser

class ConfigManager:
    """
    Gerencia as configurações do aplicativo salvas no arquivo config.ini.
    """
    def __init__(self):
        self.config_path = Path(CONFIG_FILE_NAME)
        self.config = configparser.ConfigParser()
        self._load_or_create_default()

    def _load_or_create_default(self):
        """Carrega o arquivo de configuração ou cria um com valores padrão se não existir."""
        if not self.config_path.exists():
            self.config['PADRAO'] = {
                'pasta_xml': '',
                'pasta_saida': './relatorios_nfe'
            }
            self.save()
        else:
            self.config.read(self.config_path, encoding='utf-8')

    def get(self, section: str, option: str, fallback: str = "") -> str:
        """Obtém um valor de configuração de forma segura."""
        return self.config.get(section, option, fallback=fallback)

    def set(self, section: str, option: str, value: str):
        """Define um valor de configuração."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def save(self):
        """Salva as configurações atuais no arquivo .ini."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

# Cria uma instância única para ser usada em todo o projeto
config_manager = ConfigManager()
