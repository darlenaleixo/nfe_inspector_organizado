#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo do Dashboard Web.

Utiliza Flask para criar uma interface web interativa para visualizar os resultados,
com rotas de API para servir os dados de forma eficiente.
"""
import os
import logging
import webbrowser

try:
    from flask import Flask, render_template, jsonify, request
    FLASK_OK = True
except ImportError:
    FLASK_OK = False

def iniciar_dashboard_web(processor):
    """
    Inicializa e executa o dashboard web com Flask.
    'processor' é uma instância da classe NFeProcessor.
    """
    if not FLASK_OK:
        logging.error("Flask não está instalado. Não é possível iniciar o dashboard web.")
        return
    
    # Garante que os dados sejam processados antes de iniciar o servidor
    if not processor.dados_processados and processor.pasta_xml:
        processor.processar_pasta_paralelo()
        processor.calcular_resumos()

    # Define o caminho para a pasta de templates
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app = Flask(__name__, template_folder=template_folder)

    # Anexa a instância do processador ao objeto da aplicação Flask
    # para que as rotas possam aceder aos dados.
    app.processor = processor

    @app.route("/")
    def index():
        """
        Renderiza a página HTML principal do dashboard.
        Não passa dados diretamente, pois o JavaScript irá buscá-los via API.
        """
        return render_template("dashboard.html")

    @app.route("/api/resumos")
    def api_resumos():
        """
        Endpoint da API para fornecer os dados de resumo e estatísticas.
        """
        proc = app.processor
        if not proc.resumos:
            proc.calcular_resumos() # Garante que os resumos sejam calculados
            
        resumo_completo = {
            "estatisticas": proc.estatisticas,
            "resumos": proc.resumos
        }
        return jsonify(resumo_completo)

    @app.route("/api/dados")
    def api_dados():
        """
        Endpoint da API para fornecer os dados detalhados das notas com paginação.
        Isso evita sobrecarregar o navegador com milhares de linhas de uma só vez.
        """
        proc = app.processor
        
        # Parâmetros da query para paginação (usados pelo DataTables.js)
        draw = request.args.get('draw', 1, type=int)
        start = request.args.get('start', 0, type=int)
        length = request.args.get('length', 10, type=int)
        search_value = request.args.get('search[value]', '', type=str).lower()

        # Filtra os dados com base na pesquisa
        if search_value:
            dados_filtrados = [
                linha for linha in proc.dados_processados 
                if any(search_value in str(v).lower() for v in linha.values())
            ]
        else:
            dados_filtrados = proc.dados_processados

        total_registos = len(proc.dados_processados)
        total_filtrado = len(dados_filtrados)
        
        # Aplica a paginação aos dados filtrados
        dados_pagina = dados_filtrados[start : start + length]
        
        return jsonify({
            "draw": draw,
            "recordsTotal": total_registos,
            "recordsFiltered": total_filtrado,
            "data": dados_pagina
        })

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    url = "http://127.0.0.1:5000"
    logging.info(f"Dashboard web iniciado. Acesse em: {url}")
    webbrowser.open(url)
    app.run(port=5000, debug=False)
