# -*- coding: utf-8 -*-
import os
import csv
import json
import logging
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

# --- Dependências ---
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame, PageTemplate, NextPageTemplate
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

try:
    from openpyxl.styles import Font, PatternFill, Alignment
    OPENPYXL_OK = True
except ImportError:
    OPENPYXL_OK = False

# --- Dicionário para traduzir nomes de colunas ---
COLUNAS_TRADUZIDAS = {
    'status': 'Status', 'arquivo': 'Arquivo', 'chave_acesso': 'Chave de Acesso',
    'modelo_doc': 'Modelo', 'serie': 'Série', 'numero_nf': 'Número NF',
    'data_emissao': 'Data Emissão', 'valor_total_nf': 'Valor Total NF',
    'valor_total_produtos': 'Valor Total Produtos', 'emit_cnpj': 'CNPJ Emitente',
    'emit_nome': 'Nome Emitente', 'dest_cnpj_cpf': 'CNPJ/CPF Dest.', 'dest_nome': 'Nome Dest.',
    'pagamentos': 'Pagamentos', 'item_numero': 'Nº Item', 'item_codigo': 'Cód. Item',
    'item_descricao': 'Descrição Item', 'item_cfop': 'CFOP', 'item_ncm': 'NCM',
    'item_quantidade': 'Qtd.', 'item_valor_unitario': 'Vlr. Unitário', 'item_valor_total': 'Vlr. Total Item',
    'icms_cst': 'CST ICMS', 'icms_vbc': 'BC ICMS', 'icms_picms': 'Alíq. ICMS',
    'icms_vicms': 'Valor ICMS', 'icms_vbcst': 'BC ICMS-ST', 'icms_vicmsst': 'Valor ICMS-ST',
    'ipi_vipi': 'Valor IPI', 'pis_cst': 'CST PIS', 'pis_vbc': 'BC PIS',
    'pis_ppis': 'Alíq. PIS', 'pis_vpis': 'Valor PIS', 'cofins_cst': 'CST COFINS',
    'cofins_vbc': 'BC COFINS', 'cofins_pcofins': 'Alíq. COFINS', 'cofins_vcofins': 'Valor COFINS'
}

# --- FUNÇÃO PRINCIPAL ---
def gerar_todos_relatorios(pasta_saida: str, dados: List[Dict[str, Any]], resumos: Dict[str, Any], estatisticas: Dict[str, Any]):
    os.makedirs(pasta_saida, exist_ok=True)
    logging.info("Iniciando geração de todos os relatórios...")
    _gerar_csv(pasta_saida, dados)
    _gerar_json(pasta_saida, dados)
    if REPORTLAB_OK:
        _gerar_pdf_novo_layout(pasta_saida, dados, resumos, estatisticas)
    else:
        logging.warning("Biblioteca 'reportlab' não encontrada. Geração de PDF desabilitada.")
    if OPENPYXL_OK:
        _gerar_excel_formatado(pasta_saida, dados, resumos, estatisticas)
    else:
        logging.warning("Biblioteca 'openpyxl' não encontrada. Geração de Excel formatado desabilitada.")

# --- Funções de Geração (CSV, JSON) ---
def _gerar_csv(pasta_saida, dados):
    caminho_csv = os.path.join(pasta_saida, "relatorio_detalhado.csv")
    if not dados: return
    try:
        chaves = sorted(list(set(k for d in dados for k in d.keys())))
        with open(caminho_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=chaves, extrasaction='ignore', delimiter=';')
            writer.writeheader()
            writer.writerows(dados)
        logging.info(f"Relatório CSV gerado: {caminho_csv}")
    except Exception as e:
        logging.error(f"Erro ao gerar CSV: {e}")

def _gerar_json(pasta_saida, dados):
    caminho_json = os.path.join(pasta_saida, "relatorio_detalhado.json")
    try:
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        logging.info(f"Relatório JSON gerado: {caminho_json}")
    except Exception as e:
        logging.error(f"Erro ao gerar JSON: {e}")

# --- LÓGICA PARA O PDF ---
class PageCanvas(object):
    """Classe para adicionar cabeçalho e rodapé personalizados."""
    def __init__(self, emit_info):
        self.emit_info = emit_info

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize
        
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(2*cm, h - 1.5*cm, self.emit_info.get('nome', 'N/A'))
        canvas.setFont('Helvetica', 9)
        canvas.drawString(2*cm, h - 2.0*cm, f"CNPJ: {self.emit_info.get('cnpj', 'N/A')}")
        canvas.line(2*cm, h - 2.2*cm, w - 2*cm, h - 2.2*cm)
        
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(w - 2*cm, 1.5*cm, f"Página {doc.page}")
        canvas.drawString(2*cm, 1.5*cm, f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.restoreState()

def _formatar_valor_monetario(valor):
    try: return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError): return str(valor)

def _criar_tabela_estilizada(data_list, col_widths=None):
    if not data_list: return None
    table = Table(data_list, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004C99")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F0F8FF")),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    return table

def _gerar_pdf_novo_layout(pasta_saida, dados, resumos, estatisticas):
    caminho_pdf = os.path.join(pasta_saida, "relatorio_gerencial.pdf")
    doc = SimpleDocTemplate(caminho_pdf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=3*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    story = []

    info_emitente = {'nome': dados[0].get('emit_nome'), 'cnpj': dados[0].get('emit_cnpj')} if dados else {}
    handler = PageCanvas(info_emitente)
    frame_retrato = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_retrato')
    frame_paisagem = Frame(doc.leftMargin, doc.bottomMargin, doc.height, doc.width, id='frame_paisagem')
    
    doc.addPageTemplates([
        PageTemplate(id='Retrato', frames=frame_retrato, onPage=handler, pagesize=A4),
        PageTemplate(id='Paisagem', frames=frame_paisagem, onPage=handler, pagesize=landscape(A4)),
    ])

    title_style = ParagraphStyle('Title', parent=styles['h1'], alignment=TA_CENTER, fontSize=18, spaceAfter=0.5*cm)
    section_title_style = ParagraphStyle('SectionTitle', parent=styles['h2'], fontSize=14, spaceBefore=0.8*cm, spaceAfter=0.5*cm)

    # PÁGINA 1: Resumo do Mês
    story.append(Paragraph("Relatório Mensal de Operações Fiscais", title_style))
    story.append(Paragraph("Resumo Geral do Período", section_title_style))
    kpi_data = [['Indicador', 'Valor']] + [[k, v] for k,v in {
        'Total de Vendas (Líquido)': _formatar_valor_monetario(resumos.get('total_vendas', 0)),
        'Total de Itens Vendidos': f"{resumos.get('total_itens_vendidos', 0):,}",
        'Notas Processadas': f"{estatisticas.get('notas_processadas_sucesso', 0):,}",
    }.items()]
    story.append(_criar_tabela_estilizada(kpi_data))

    # PÁGINA 2: Apuração Fiscal e Auditoria (Paisagem)
    story.append(NextPageTemplate('Paisagem'))
    story.append(PageBreak())
    story.append(Paragraph("Detalhes Fiscais e Auditoria", title_style))
    
    df_apuracao = pd.DataFrame(resumos.get('apuracao_impostos', {})).T.reset_index().rename(columns={'index':'CFOP'})
    if not df_apuracao.empty:
        story.append(Paragraph("Apuração de Impostos por CFOP", section_title_style))
        for col in df_apuracao.columns[1:]: df_apuracao[col] = df_apuracao[col].apply(_formatar_valor_monetario)
        data_apuracao = [df_apuracao.columns.tolist()] + df_apuracao.values.tolist()
        story.append(_criar_tabela_estilizada(data_apuracao))
    
    auditoria = resumos.get('auditoria_aliquotas', [])
    if auditoria:
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Auditoria de Alíquotas de ICMS", section_title_style))
        data_auditoria = [['NF', 'Produto', 'NCM', 'Alíq. Declarada (%)', 'Alíq. Esperada (%)']]
        for item in auditoria:
            data_auditoria.append([
                item.get('numero_nf'), item.get('item_descricao'), item.get('item_ncm'),
                f"{item.get('icms_picms', 0):.2f}", f"{item.get('aliquota_esperada', 0):.2f}",
            ])
        story.append(_criar_tabela_estilizada(data_auditoria))

    try:
        doc.build(story)
        logging.info(f"Relatório PDF com novo layout gerado: {caminho_pdf}")
    except Exception as e:
        logging.error(f"Erro ao construir o documento PDF: {e}")

# --- LÓGICA PARA O EXCEL ---
def _gerar_excel_formatado(pasta_saida, dados, resumos, estatisticas):
    caminho_excel = os.path.join(pasta_saida, "relatorio_completo_formatado.xlsx")
    try:
        with pd.ExcelWriter(caminho_excel, engine='openpyxl') as writer:
            _criar_aba_dashboard_excel(writer, resumos, estatisticas)
            
            # Aba de Auditoria de ICMS
            auditoria_df = pd.DataFrame(resumos.get('auditoria_aliquotas', []))
            if not auditoria_df.empty:
                auditoria_df.to_excel(writer, sheet_name='Auditoria ICMS', index=False, startrow=1)
                _formatar_aba_excel(writer.sheets['Auditoria ICMS'], "Divergências de Alíquotas de ICMS")

            # Outras abas...
            df_apuracao = pd.DataFrame(resumos.get('apuracao_impostos', {}))
            if not df_apuracao.empty:
                df_apuracao.index.name = 'CFOP'
                df_apuracao.reset_index(inplace=True)
                df_apuracao.to_excel(writer, sheet_name='Apuracao por CFOP', index=False, startrow=1)
                _formatar_aba_excel(writer.sheets['Apuracao por CFOP'], "Apuração de Impostos por CFOP")
            
            df_traduzido = pd.DataFrame(dados).rename(columns=COLUNAS_TRADUZIDAS)
            df_traduzido.to_excel(writer, sheet_name='Dados Completos', index=False, startrow=1)
            _formatar_aba_excel(writer.sheets['Dados Completos'], "Dados Detalhados das Notas Fiscais")

        logging.info(f"Relatório Excel formatado gerado: {caminho_excel}")
    except Exception as e:
        logging.error(f"Erro ao gerar Excel formatado: {e}")

def _criar_aba_dashboard_excel(writer, resumos, estatisticas):
    ws = writer.book.create_sheet("Dashboard", 0)
    ws['B2'] = "Dashboard de Análise de Notas Fiscais"
    ws['B2'].font = Font(size=18, bold=True, color="000080")
    kpis = {
        "Total de Vendas": resumos.get('total_vendas', 0),
        "Total de Itens Vendidos": resumos.get('total_itens_vendidos', 0),
        "Notas Processadas": estatisticas.get('notas_processadas_sucesso', 0),
    }
    row = 5
    for key, value in kpis.items():
        ws[f'B{row}'] = key; ws[f'C{row}'] = value
        ws[f'B{row}'].font = Font(bold=True)
        ws[f'C{row}'].alignment = Alignment(horizontal='right')
        if "Vendas" in key: ws[f'C{row}'].number_format = 'R$ #,##0.00'
        row += 1
    ws.column_dimensions['B'].width = 30; ws.column_dimensions['C'].width = 20

def _formatar_aba_excel(ws, titulo):
    ws.insert_rows(1); ws['A1'] = titulo
    ws['A1'].font = Font(size=16, bold=True, color="000080")
    header_fill = PatternFill(start_color="000080", end_color="000080", fill_type="solid")
    for cell in ws[2]:
        cell.font = Font(bold=True, color="FFFFFF"); cell.fill = header_fill
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length: max_length = len(str(cell.value))
            except: pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
    for col in ws.iter_cols(min_row=3):
        col_letter = col[0].column_letter
        header_text = str(ws[f'{col_letter}2'].value).lower()
        if any(term in header_text for term in ["valor", "icms", "ipi", "pis", "cofins"]):
            for cell in col:
                if isinstance(cell.value, (int, float)): cell.number_format = 'R$ #,##0.00'

