#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI completa e funcional para o Sistema de Download
"""

import click
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional
from tabulate import tabulate
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from nfe_download_service_final import NFeDownloadService, Cliente
from sefaz_client_completo import SefazWebserviceClient
from sefaz.auth import CertificateManager


def setup_logging(verbose: bool = False):
    """Configura sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Formato com cores para terminal
    if sys.stdout.isatty():
        format_str = '%(asctime)s - \033[1m%(levelname)s\033[0m - %(message)s'
    else:
        format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt='%H:%M:%S'
    )
    
    # Silenciar logs verbosos de bibliotecas
    if not verbose:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('zeep').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Modo verboso com logs detalhados')
@click.option('--config', default='config.ini', help='Arquivo de configuração')
@click.pass_context
def cli(ctx, verbose, config):
    """🚀 Sistema de Download de NFe/NFSe para Clientes"""
    
    # Configurar logging
    setup_logging(verbose)
    
    # Verificar se arquivo de configuração existe
    if not os.path.exists(config):
        click.echo(f"⚠️  Arquivo de configuração não encontrado: {config}")
        click.echo("📋 Use 'nfe-cli config exemplo' para criar um arquivo de exemplo")
    
    # Criar contexto compartilhado
    ctx.ensure_object(dict)
    ctx.obj['service'] = NFeDownloadService()
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config


# ==================== COMANDOS DE CLIENTE ====================

@cli.group()
def cliente():
    """👥 Comandos para gerenciamento de clientes"""
    pass


@cliente.command('add')
@click.option('--id', 'cliente_id', required=True, 
              help='ID único do cliente (ex: empresa_abc)')
@click.option('--cnpj', required=True, 
              help='CNPJ do cliente (apenas números)')
@click.option('--razao-social', required=True, 
              help='Razão social completa da empresa')
@click.option('--certificado', required=True, type=click.Path(exists=True),
              help='Caminho para o arquivo .pfx ou .p12')
@click.option('--senha', required=True, hide_input=True, 
              confirmation_prompt=True, help='Senha do certificado')
@click.option('--uf', required=True, type=click.Choice([
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]), help='UF do cliente')
@click.option('--ambiente', type=click.Choice(['1', '2']), default='2', 
              help='Ambiente: 1=Produção, 2=Homologação (padrão)')
@click.option('--observacoes', default='', 
              help='Observações sobre o cliente')
@click.pass_context
def add_cliente(ctx, cliente_id, cnpj, razao_social, certificado, 
               senha, uf, ambiente, observacoes):
    """➕ Adiciona um novo cliente"""
    
    service = ctx.obj['service']
    
    # Limpar CNPJ
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj_limpo) != 14:
        click.echo("❌ CNPJ deve ter 14 dígitos", err=True)
        return
    
    # Validar certificado
    click.echo("🔍 Validando certificado...")
    try:
        cert_manager = CertificateManager(certificado, senha)
        cert_files = cert_manager.get_cert_files()
        click.echo(f"✅ Certificado válido")
        
        # Testar conectividade SEFAZ (opcional)
        if click.confirm("🌐 Testar conectividade com SEFAZ?"):
            sefaz_client = SefazWebserviceClient(uf, int(ambiente), cert_manager)
            if sefaz_client.testar_conectividade():
                click.echo("✅ Conectividade SEFAZ OK")
            else:
                click.echo("⚠️  Falha na conectividade SEFAZ (mas certificado é válido)")
                
    except Exception as e:
        click.echo(f"❌ Erro no certificado: {e}", err=True)
        return
    
    # Criar cliente
    cliente = Cliente(
        id=cliente_id,
        cnpj=cnpj_limpo,
        razao_social=razao_social,
        certificado_path=os.path.abspath(certificado),
        certificado_senha=senha,
        uf=uf.upper(),
        ambiente=int(ambiente),
        observacoes=observacoes
    )
    
    # Salvar no banco
    if service.cliente_manager.adicionar_cliente(cliente):
        click.echo(f"✅ Cliente '{cliente_id}' adicionado com sucesso!")
        click.echo(f"   📋 {razao_social}")
        click.echo(f"   🏢 CNPJ: {cnpj_limpo}")
        click.echo(f"   📍 UF: {uf} (Ambiente: {'Produção' if ambiente == '1' else 'Homologação'})")
    else:
        click.echo(f"❌ Erro ao adicionar cliente '{cliente_id}'", err=True)


@cliente.command('list')
@click.option('--formato', type=click.Choice(['tabela', 'json', 'csv']), 
              default='tabela', help='Formato de saída')
@click.option('--todos/--apenas-ativos', default=False, 
              help='Mostrar todos os clientes ou apenas ativos')
@click.pass_context
def list_clientes(ctx, formato, todos):
    """📋 Lista clientes cadastrados"""
    
    service = ctx.obj['service']
    clientes = service.cliente_manager.listar_clientes(apenas_ativos=not todos)
    
    if not clientes:
        click.echo("📭 Nenhum cliente encontrado.")
        return
    
    if formato == 'json':
        # Ocultar senhas no JSON
        clientes_json = []
        for c in clientes:
            cliente_dict = c.__dict__.copy()
            cliente_dict['certificado_senha'] = '***'
            clientes_json.append(cliente_dict)
        
        click.echo(json.dumps(clientes_json, indent=2, ensure_ascii=False))
    
    elif formato == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(['ID', 'CNPJ', 'Razão Social', 'UF', 'Ambiente', 
                        'Ativo', 'Último Download', 'Observações'])
        
        # Dados
        for c in clientes:
            ultimo_dl = c.ultimo_download[:19] if c.ultimo_download else 'Nunca'
            ambiente_str = 'Produção' if c.ambiente == 1 else 'Homologação'
            
            writer.writerow([
                c.id, c.cnpj, c.razao_social, c.uf, ambiente_str,
                'Sim' if c.ativo else 'Não', ultimo_dl, c.observacoes
            ])
        
        click.echo(output.getvalue())
    
    else:  # tabela
        headers = ['ID', 'CNPJ', 'Razão Social', 'UF', 'Amb', 'Status', 'Último Download']
        rows = []
        
        for c in clientes:
            # Formatar dados
            cnpj_fmt = f"{c.cnpj[:2]}.{c.cnpj[2:5]}.{c.cnpj[5:8]}/{c.cnpj[8:12]}-{c.cnpj[12:14]}"
            ultimo_dl = c.ultimo_download[:16] if c.ultimo_download else 'Nunca'
            ambiente_str = 'PROD' if c.ambiente == 1 else 'HML'
            status_str = '🟢 Ativo' if c.ativo else '🔴 Inativo'
            
            rows.append([
                c.id, cnpj_fmt, c.razao_social[:25], c.uf, 
                ambiente_str, status_str, ultimo_dl
            ])
        
        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        click.echo(f"\n📊 Total: {len(clientes)} clientes")


@cliente.command('info')
@click.argument('cliente_id')
@click.pass_context
def info_cliente(ctx, cliente_id):
    """ℹ️  Informações detalhadas de um cliente"""
    
    service = ctx.obj['service']
    cliente = service.cliente_manager.obter_cliente(cliente_id)
    
    if not cliente:
        click.echo(f"❌ Cliente '{cliente_id}' não encontrado", err=True)
        return
    
    # Informações básicas
    click.echo(f"👤 Informações do Cliente")
    click.echo("=" * 50)
    click.echo(f"ID: {cliente.id}")
    click.echo(f"CNPJ: {cliente.cnpj[:2]}.{cliente.cnpj[2:5]}.{cliente.cnpj[5:8]}/{cliente.cnpj[8:12]}-{cliente.cnpj[12:14]}")
    click.echo(f"Razão Social: {cliente.razao_social}")
    click.echo(f"UF: {cliente.uf}")
    click.echo(f"Ambiente: {'Produção' if cliente.ambiente == 1 else 'Homologação'}")
    click.echo(f"Status: {'🟢 Ativo' if cliente.ativo else '🔴 Inativo'}")
    click.echo(f"Certificado: {cliente.certificado_path}")
    click.echo(f"Último Download: {cliente.ultimo_download or 'Nunca'}")
    
    if cliente.observacoes:
        click.echo(f"Observações: {cliente.observacoes}")
    
    # Estatísticas de download
    try:
        import sqlite3
        with sqlite3.connect(service.cliente_manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as total, SUM(valor_total) as valor_total
                FROM notas_baixadas WHERE cliente_id = ?
            """, (cliente_id,))
            
            row = cursor.fetchone()
            if row and row[0] > 0:
                click.echo(f"\n📈 Estatísticas de Download")
                click.echo(f"Total de notas baixadas: {row[0]}")
                click.echo(f"Valor total: R$ {row[1]:,.2f}" if row[1] else "Valor total: R$ 0,00")
    except:
        pass


@cliente.command('remove')
@click.argument('cliente_id')
@click.confirmation_option(
    prompt='⚠️  Tem certeza que deseja remover este cliente?'
)
@click.pass_context
def remove_cliente(ctx, cliente_id):
    """🗑️  Remove um cliente (marca como inativo)"""
    
    service = ctx.obj['service']
    cliente = service.cliente_manager.obter_cliente(cliente_id)
    
    if not cliente:
        click.echo(f"❌ Cliente '{cliente_id}' não encontrado", err=True)
        return
    
    cliente.ativo = False
    if service.cliente_manager.adicionar_cliente(cliente):
        click.echo(f"✅ Cliente '{cliente_id}' removido com sucesso")
    else:
        click.echo(f"❌ Erro ao remover cliente '{cliente_id}'", err=True)


# ==================== COMANDOS DE DOWNLOAD ====================

@cli.group()
def download():
    """📥 Comandos para download de notas fiscais"""
    pass


@download.command('nfe')
@click.argument('cliente_id')
@click.option('--data-inicio', required=True, 
              help='Data início (YYYY-MM-DD)')
@click.option('--data-fim', required=True, 
              help='Data fim (YYYY-MM-DD)')
@click.option('--manifestar/--nao-manifestar', default=False,
              help='Manifestar ciência automaticamente')
@click.pass_context
def download_nfe(ctx, cliente_id, data_inicio, data_fim, manifestar):
    """📄 Download de NFe de um cliente específico"""
    
    service = ctx.obj['service']
    
    # Validar cliente
    cliente = service.cliente_manager.obter_cliente(cliente_id)
    if not cliente:
        click.echo(f"❌ Cliente '{cliente_id}' não encontrado", err=True)
        return
    
    # Validar datas
    try:
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        
        if dt_inicio > dt_fim:
            click.echo("❌ Data início deve ser anterior à data fim", err=True)
            return
            
        if (dt_fim - dt_inicio).days > 365:
            click.echo("⚠️  Período muito longo (máximo 1 ano recomendado)")
            if not click.confirm("Continuar mesmo assim?"):
                return
                
    except ValueError:
        click.echo("❌ Formato de data inválido. Use YYYY-MM-DD", err=True)
        return
    
    # Mostrar informações do download
    click.echo(f"🚀 Iniciando download de NFe")
    click.echo(f"👤 Cliente: {cliente.razao_social}")
    click.echo(f"📅 Período: {data_inicio} a {data_fim}")
    click.echo(f"🏢 UF: {cliente.uf} ({'Produção' if cliente.ambiente == 1 else 'Homologação'})")
    click.echo(f"📋 Manifestar ciência: {'Sim' if manifestar else 'Não'}")
    click.echo("-" * 60)
    
    try:
        # Executar download
        with click.progressbar(length=100, label='Processando') as bar:
            job = service.download_notas_cliente(
                cliente_id=cliente_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                tipo_nota='nfe',
                manifestar_automatico=manifestar
            )
            bar.update(100)
        
        # Mostrar resultado
        click.echo()
        if job.status == 'concluido':
            click.echo(f"✅ Download concluído com sucesso!")
            click.echo(f"📊 Resultado:")
            click.echo(f"   📄 Total de manifestações: {job.total_notas}")
            click.echo(f"   ✅ Notas baixadas: {job.notas_baixadas}")
            
            if job.notas_com_erro > 0:
                click.echo(f"   ❌ Notas com erro: {job.notas_com_erro}")
            
            # Mostrar localização dos arquivos
            if 'pasta_xml' in (job.detalhes or {}):
                click.echo(f"📁 Arquivos salvos em: {job.detalhes['pasta_xml']}")
        
        elif job.status == 'erro':
            click.echo(f"❌ Erro no download: {job.erro_msg}", err=True)
            
    except KeyboardInterrupt:
        click.echo("\n⏹️  Download interrompido pelo usuário")
    except Exception as e:
        click.echo(f"\n❌ Erro inesperado: {e}", err=True)


@download.command('lote')
@click.option('--clientes', 
              help='IDs dos clientes separados por vírgula (ou todos se omitido)')
@click.option('--data-inicio', required=True, 
              help='Data início (YYYY-MM-DD)')
@click.option('--data-fim', required=True, 
              help='Data fim (YYYY-MM-DD)')
@click.option('--threads', default=3, type=click.IntRange(1, 10),
              help='Número de threads paralelas (1-10)')
@click.option('--manifestar/--nao-manifestar', default=False,
              help='Manifestar ciência automaticamente')
@click.pass_context
def download_lote(ctx, clientes, data_inicio, data_fim, threads, manifestar):
    """📦 Download em lote para múltiplos clientes"""
    
    service = ctx.obj['service']
    
    # Definir lista de clientes
    if clientes:
        clientes_ids = [c.strip() for c in clientes.split(',')]
        
        # Validar se todos existem
        clientes_invalidos = []
        for cliente_id in clientes_ids:
            if not service.cliente_manager.obter_cliente(cliente_id):
                clientes_invalidos.append(cliente_id)
        
        if clientes_invalidos:
            click.echo(f"❌ Clientes não encontrados: {', '.join(clientes_invalidos)}", err=True)
            return
    else:
        # Todos os clientes ativos
        todos_clientes = service.cliente_manager.listar_clientes(apenas_ativos=True)
        clientes_ids = [c.id for c in todos_clientes]
    
    if not clientes_ids:
        click.echo("📭 Nenhum cliente encontrado para download", err=True)
        return
    
    # Confirmar operação
    click.echo(f"📦 Download em lote")
    click.echo(f"👥 Clientes: {len(clientes_ids)}")
    click.echo(f"📅 Período: {data_inicio} a {data_fim}")
    click.echo(f"🔀 Threads: {threads}")
    click.echo(f"📋 Manifestar ciência: {'Sim' if manifestar else 'Não'}")
    
    if not click.confirm("\n🚀 Iniciar download em lote?"):
        return
    
    click.echo("-" * 60)
    
    try:
        # Executar downloads
        jobs = service.download_lote_clientes(
            clientes_ids=clientes_ids,
            data_inicio=data_inicio,
            data_fim=data_fim,
            max_workers=threads,
            manifestar_automatico=manifestar
        )
        
        # Analisar resultados
        sucessos = 0
        erros = 0
        total_notas = 0
        
        click.echo(f"\n📊 Resultados do lote:")
        click.echo("=" * 80)
        
        for job in jobs:
            cliente = service.cliente_manager.obter_cliente(job.cliente_id)
            nome_cliente = cliente.razao_social[:35] if cliente else job.cliente_id
            
            if job.status == 'concluido':
                click.echo(f"✅ {nome_cliente:<35} | {job.notas_baixadas:>3}/{job.total_notas:<3} notas")
                sucessos += 1
                total_notas += job.notas_baixadas
            else:
                erro_msg = job.erro_msg[:40] + "..." if len(job.erro_msg) > 40 else job.erro_msg
                click.echo(f"❌ {nome_cliente:<35} | {erro_msg}")
                erros += 1
        
        click.echo("=" * 80)
        click.echo(f"📈 Resumo Final:")
        click.echo(f"   ✅ Sucessos: {sucessos}")
        click.echo(f"   ❌ Erros: {erros}")
        click.echo(f"   📄 Total de notas baixadas: {total_notas}")
        
    except KeyboardInterrupt:
        click.echo("\n⏹️  Download em lote interrompido pelo usuário")
    except Exception as e:
        click.echo(f"\n❌ Erro inesperado: {e}", err=True)


@download.command('mes')
@click.argument('cliente_id')
@click.option('--mes', type=int, help='Mês (1-12, padrão: mês anterior)')
@click.option('--ano', type=int, help='Ano (padrão: ano atual)')
@click.option('--manifestar/--nao-manifestar', default=False,
              help='Manifestar ciência automaticamente')
@click.pass_context
def download_mes(ctx, cliente_id, mes, ano, manifestar):
    """📅 Download das notas de um mês específico"""
    
    hoje = datetime.now()
    
    # Definir mês/ano padrão (mês anterior)
    if not ano:
        ano = hoje.year
    if not mes:
        mes = hoje.month - 1
        if mes == 0:
            mes = 12
            ano -= 1
    
    # Validar mês
    if not (1 <= mes <= 12):
        click.echo("❌ Mês deve estar entre 1 e 12", err=True)
        return
    
    # Calcular período
    from calendar import monthrange
    data_inicio = f"{ano:04d}-{mes:02d}-01"
    ultimo_dia = monthrange(ano, mes)[1]
    data_fim = f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"
    
    # Chamar comando download normal
    ctx.invoke(download_nfe, 
               cliente_id=cliente_id,
               data_inicio=data_inicio,
               data_fim=data_fim,
               manifestar=manifestar)


# ==================== COMANDOS UTILITÁRIOS ====================

@cli.command('status')
@click.pass_context
def status_sistema(ctx):
    """📊 Status geral do sistema"""
    
    service = ctx.obj['service']
    
    try:
        # Estatísticas dos clientes
        clientes = service.cliente_manager.listar_clientes(apenas_ativos=False)
        clientes_ativos = [c for c in clientes if c.ativo]
        
        click.echo("📊 Status do Sistema de Download")
        click.echo("=" * 60)
        click.echo(f"👥 Clientes cadastrados: {len(clientes)}")
        click.echo(f"🟢 Clientes ativos: {len(clientes_ativos)}")
        click.echo(f"🔴 Clientes inativos: {len(clientes) - len(clientes_ativos)}")
        
        # Estatísticas de download
        stats = service.obter_estatisticas_downloads()
        geral = stats.get('geral', {})
        
        click.echo(f"\n📄 Estatísticas de Download:")
        click.echo(f"   Total de notas baixadas: {geral.get('total_notas', 0)}")
        click.echo(f"   Clientes com downloads: {geral.get('total_clientes', 0)}")
        click.echo(f"   Valor total: R$ {geral.get('valor_total_geral', 0):,.2f}")
        click.echo(f"   Notas manifestadas: {geral.get('notas_manifestadas', 0)}")
        
        # Por tipo de nota
        por_tipo = stats.get('por_tipo', {})
        if por_tipo:
            click.echo(f"\n📋 Por tipo de nota:")
            for tipo, quantidade in por_tipo.items():
                click.echo(f"   {tipo.upper()}: {quantidade}")
        
        # Clientes mais ativos
        por_cliente = stats.get('por_cliente', [])
        if por_cliente:
            click.echo(f"\n🏆 Top 5 clientes (por volume):")
            for i, cliente in enumerate(por_cliente[:5], 1):
                nome = cliente['razao_social'] or cliente['cliente_id']
                click.echo(f"   {i}. {nome[:30]:<30} | {cliente['total_notas']:>4} notas")
        
        # Jobs recentes
        jobs_recentes = stats.get('jobs_recentes', [])
        if jobs_recentes:
            click.echo(f"\n⏰ Últimos downloads:")
            for job in jobs_recentes[:5]:
                data_job = job['criado_em'][:16] if job['criado_em'] else 'N/A'
                status_icon = '✅' if job['status'] == 'concluido' else '❌'
                click.echo(f"   {status_icon} {job['cliente_id']:<15} | {data_job} | {job['notas_baixadas']}/{job['total_notas']} notas")
                
    except Exception as e:
        click.echo(f"❌ Erro ao obter estatísticas: {e}", err=True)


@cli.command('test')
@click.argument('certificado_path', type=click.Path(exists=True))
@click.option('--senha', required=True, hide_input=True, 
              help='Senha do certificado')
@click.option('--uf', default='RJ', help='UF para teste')
@click.option('--ambiente', type=click.Choice(['1', '2']), default='2',
              help='Ambiente para teste')
def test_certificado(certificado_path, senha, uf, ambiente):
    """🔧 Testa certificado e conectividade SEFAZ"""
    
    click.echo(f"🔍 Testando certificado: {os.path.basename(certificado_path)}")
    click.echo(f"🏢 UF: {uf} (Ambiente: {'Produção' if ambiente == '1' else 'Homologação'})")
    click.echo("-" * 50)
    
    try:
        # Testar extração do certificado
        click.echo("1️⃣  Testando extração do certificado...")
        cert_manager = CertificateManager(certificado_path, senha)
        cert_files = cert_manager.get_cert_files()
        click.echo(f"   ✅ Certificado extraído para: {os.path.basename(cert_files[0])}")
        
        # Testar conectividade com SEFAZ
        click.echo("2️⃣  Testando conectividade SEFAZ...")
        sefaz_client = SefazWebserviceClient(
            uf=uf, 
            ambiente=int(ambiente), 
            cert_manager=cert_manager
        )
        
        if sefaz_client.testar_conectividade():
            click.echo("   ✅ Conectividade SEFAZ OK")
        else:
            click.echo("   ❌ Falha na conectividade SEFAZ")
        
        click.echo("\n🎉 Teste concluído!")
        
    except Exception as e:
        click.echo(f"   ❌ Erro no teste: {e}", err=True)


@cli.command('config')
@click.argument('acao', type=click.Choice(['exemplo', 'mostrar']))
def config_comando(acao):
    """⚙️  Gerencia configuração do sistema"""
    
    if acao == 'exemplo':
        # Criar arquivo de configuração de exemplo
        config_exemplo = """# Configuração do Sistema de Download NFe/NFSe

[PADRAO]
# Pasta onde serão salvos os downloads
pasta_saida = downloads_clientes

[DOWNLOAD]
# Número máximo de threads para downloads paralelos
max_threads = 3

# Timeout para requisições SOAP (segundos)
timeout_soap = 60

# Intervalo entre requisições (segundos)
intervalo_requisicoes = 1

[SEFAZ]
# UF padrão para operações
uf = RJ

# Ambiente padrão: 1=Produção, 2=Homologação  
ambiente = 2

# Verificar certificados SSL
verificar_ssl = true

[MANIFESTACAO]
# Manifestar ciência automaticamente
manifestar_automatico = false

# Tipo de manifestação padrão
tipo_manifestacao_padrao = 210210

[LOGGING]
# Nível de log: DEBUG, INFO, WARNING, ERROR
nivel = INFO

[BANCO]
# Caminho para banco SQLite
caminho_db = clientes.db
"""
        
        with open('config_exemplo.ini', 'w', encoding='utf-8') as f:
            f.write(config_exemplo)
        
        click.echo("✅ Arquivo 'config_exemplo.ini' criado!")
        click.echo("📋 Copie para 'config.ini' e edite conforme necessário")
        
    elif acao == 'mostrar':
        # Mostrar configuração atual
        try:
            from core.config import ConfigManager
            config = ConfigManager()
            
            click.echo("⚙️  Configuração Atual")
            click.echo("=" * 50)
            click.echo(f"Pasta Saída: {config.get('PADRAO', 'pasta_saida', 'downloads_clientes')}")
            click.echo(f"UF Padrão: {config.get('SEFAZ', 'uf', 'RJ')}")
            click.echo(f"Ambiente: {config.get('SEFAZ', 'ambiente', '2')}")
            click.echo(f"Verificar SSL: {config.get_boolean('SEFAZ', 'verificar_ssl', True)}")
            click.echo(f"Max Threads: {config.get('DOWNLOAD', 'max_threads', '3')}")
            
        except Exception as e:
            click.echo(f"❌ Erro ao ler configuração: {e}", err=True)


if __name__ == '__main__':
    cli()