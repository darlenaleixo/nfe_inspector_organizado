# -*- coding: utf-8 -*-
import logging
import traceback
import os
import hashlib
import pickle
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

@contextmanager
def error_handler(operation_name: str):
    """Gestor de contexto para tratamento de erros centralizado."""
    try:
        yield
    except FileNotFoundError as e:
        logging.error(f"Arquivo não encontrado em {operation_name}: {e}")
    except PermissionError as e:
        logging.error(f"Erro de permissão em {operation_name}: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado em {operation_name}: {e}")
        logging.debug(traceback.format_exc())

class CacheManager:
    """
    Gere o cache dos resultados do processamento de XML para acelerar reanálises.
    """
    def __init__(self, cache_dir: str = ".nfe_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logging.info(f"Cache de arquivos será armazenado em: {self.cache_dir.resolve()}")

    def _get_cache_key(self, filepath: str) -> str:
        """
        Gera uma chave de cache única baseada no caminho, tamanho e data de modificação do arquivo.
        """
        try:
            stats = os.stat(filepath)
            # Combina o caminho, o tamanho e o tempo de modificação para criar um hash
            key_source = f"{filepath}-{stats.st_size}-{stats.st_mtime}"
            return hashlib.md5(key_source.encode('utf-8')).hexdigest()
        except FileNotFoundError:
            return ""

    def get(self, filepath: str) -> Optional[List[Dict[str, Any]]]:
        """
        Tenta obter os dados processados de um arquivo a partir do cache.
        Retorna os dados se encontrados e válidos, caso contrário, None.
        """
        cache_key = self._get_cache_key(filepath)
        if not cache_key:
            return None
            
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    logging.debug(f"Cache HIT para o arquivo: {os.path.basename(filepath)}")
                    return pickle.load(f)
            except (pickle.UnpicklingError, EOFError) as e:
                logging.warning(f"Cache corrompido para {os.path.basename(filepath)}. O arquivo será reprocessado. Erro: {e}")
                # Remove o arquivo de cache corrompido
                os.remove(cache_file)
        
        logging.debug(f"Cache MISS para o arquivo: {os.path.basename(filepath)}")
        return None

    def set(self, filepath: str, data: List[Dict[str, Any]]):
        """
        Salva os dados processados de um arquivo no cache.
        """
        cache_key = self._get_cache_key(filepath)
        if not cache_key:
            return

        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logging.error(f"Não foi possível salvar o cache para {os.path.basename(filepath)}: {e}")

