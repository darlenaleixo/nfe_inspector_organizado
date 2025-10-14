# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any

# Namespace único para NFe/NFC-e
NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

def _sanitizar(texto: str) -> str:
    """Limpa uma string, removendo caracteres de controlo e espaços excessivos."""
    if not isinstance(texto, str):
        return ""
    # Remove caracteres não imprimíveis, exceto nova linha e tabulação
    texto_limpo = "".join(char for char in texto if char.isprintable() or char in '\n\r\t')
    # Substitui múltiplos espaços/quebras de linha por um único espaço
    return " ".join(texto_limpo.split()).strip()

def _text(node: Optional[ET.Element]) -> str:
    """Extrai e sanitiza o texto de um elemento XML de forma segura."""
    return _sanitizar(node.text) if (node is not None and node.text) else ""

def _find(node: ET.Element, path: str) -> Optional[ET.Element]:
    """Busca um elemento XML usando o namespace padrão."""
    return node.find(path, NS)

def _findall(node: ET.Element, path: str) -> List[ET.Element]:
    """Busca todos os elementos XML usando o namespace padrão."""
    return node.findall(path, NS)

def _parse_float(s: Any) -> float:
    """Converte uma string para float de forma segura."""
    if not s:
        return 0.0
    try:
        return float(str(s).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0

def parse_nfe_nfce_xml(fp: str, chaves_canceladas: set) -> Optional[List[Dict[str, Any]]]:
    """Lê um XML de NFe/NFCe e extrai todas as informações de forma robusta."""
    try:
        tree = ET.parse(fp)
        r = tree.getroot()
    except ET.ParseError:
        return None

    infNFe = _find(r, ".//nfe:infNFe")
    if infNFe is None:
        return None # Não é uma NFe/NFCe válida

    ide = _find(infNFe, "nfe:ide")
    emit = _find(infNFe, "nfe:emit")
    det_list = _findall(infNFe, "nfe:det")

    if not all([ide, emit, det_list]):
        return None # Estrutura mínima não encontrada

    # --- Dados Gerais da Nota ---
    chave = infNFe.attrib.get("Id", "").replace("NFe", "")
    enderEmit = _find(emit, "nfe:enderEmit") or ET.Element("enderEmit")
    dest = _find(infNFe, "nfe:dest") or ET.Element("dest")
    total = _find(infNFe, "nfe:total/nfe:ICMSTot") or ET.Element("ICMSTot")
    pag = _find(infNFe, "nfe:pag") or ET.Element("pag")
    
    mapa_pagamento = {
        "01": "Dinheiro", "02": "Cheque", "03": "Cartão de Crédito", "04": "Cartão de Débito",
        "05": "Crédito Loja", "10": "Vale Alimentação", "11": "Vale Refeição", "12": "Vale Presente",
        "13": "Vale Combustível", "14": "Duplicata Mercantil", "15": "Boleto Bancário", "16": "Depósito Bancário",
        "17": "PIX", "18": "Transferência Bancária", "19": "Carteira Digital", "90": "Sem Pagamento", "99": "Outros"
    }
    pagamentos_list = [
        f"{mapa_pagamento.get(_text(_find(detPag, 'nfe:tPag')), 'Outros')}={_text(_find(detPag, 'nfe:vPag'))}"
        for detPag in _findall(pag, "nfe:detPag")
    ]

    dados_comuns = {
        "status": "Cancelada" if chave in chaves_canceladas else "Autorizada",
        "arquivo": os.path.basename(fp),
        "chave_acesso": chave,
        "modelo_doc": _text(_find(ide, "nfe:mod")),
        "serie": _text(_find(ide, "nfe:serie")),
        "numero_nf": _text(_find(ide, "nfe:nNF")),
        "data_emissao": _text(_find(ide, "nfe:dhEmi")),
        "valor_total_nf": _parse_float(_text(_find(total, "nfe:vNF"))),
        "valor_total_produtos": _parse_float(_text(_find(total, "nfe:vProd"))),
        "emit_cnpj": _text(_find(emit, "nfe:CNPJ")),
        "emit_nome": _text(_find(emit, "nfe:xNome")),
        "dest_cnpj_cpf": _text(_find(dest, "nfe:CPF")) or _text(_find(dest, "nfe:CNPJ")),
        "dest_nome": _text(_find(dest, "nfe:xNome")),
        "pagamentos": "; ".join(pagamentos_list),
    }

    # --- Processamento por Item ---
    linhas_finais = []
    for det in det_list:
        prod = _find(det, "nfe:prod")
        imposto = _find(det, "nfe:imposto")

        item_dados = {
            "item_numero": det.attrib.get("nItem", ""),
            "item_codigo": _text(_find(prod, "nfe:cProd")),
            "item_descricao": _text(_find(prod, "nfe:xProd")),
            "item_cfop": _text(_find(prod, "nfe:CFOP")),
            "item_ncm": _text(_find(prod, "nfe:NCM")),
            "item_quantidade": _parse_float(_text(_find(prod, "nfe:qCom"))),
            "item_valor_unitario": _parse_float(_text(_find(prod, "nfe:vUnCom"))),
            "item_valor_total": _parse_float(_text(_find(prod, "nfe:vProd"))),
        }

        # --- EXTRAÇÃO DE IMPOSTOS ROBUSTA E COMPLETA ---
        impostos_item = {}
        if imposto is not None:
            # Itera sobre todos os filhos diretos da tag <imposto>
            for imposto_detalhe in imposto:
                # ICMS
                if 'ICMS' in imposto_detalhe.tag:
                    # A tag de detalhe (ICMS00, ICMS10, etc.) é o primeiro e único filho de <ICMS>
                    icms_grupo = imposto_detalhe[0] if len(imposto_detalhe) > 0 else None
                    if icms_grupo is not None:
                        impostos_item["icms_cst"] = _text(_find(icms_grupo, "nfe:CST")) or _text(_find(icms_grupo, "nfe:CSOSN"))
                        impostos_item["icms_vbc"] = _parse_float(_text(_find(icms_grupo, "nfe:vBC")))
                        impostos_item["icms_picms"] = _parse_float(_text(_find(icms_grupo, "nfe:pICMS")))
                        impostos_item["icms_vicms"] = _parse_float(_text(_find(icms_grupo, "nfe:vICMS")))
                        impostos_item["icms_vbcst"] = _parse_float(_text(_find(icms_grupo, "nfe:vBCST")))
                        impostos_item["icms_vicmsst"] = _parse_float(_text(_find(icms_grupo, "nfe:vICMSST")))
                # IPI
                if 'IPI' in imposto_detalhe.tag:
                    ipi_grupo = _find(imposto_detalhe, "nfe:IPITrib")
                    if ipi_grupo is not None:
                        impostos_item["ipi_vipi"] = _parse_float(_text(_find(ipi_grupo, "nfe:vIPI")))
                # PIS
                if 'PIS' in imposto_detalhe.tag:
                    pis_grupo = imposto_detalhe[0] if len(imposto_detalhe) > 0 else None # PISAliq, PISOutr, etc.
                    if pis_grupo is not None:
                        impostos_item["pis_cst"] = _text(_find(pis_grupo, "nfe:CST"))
                        impostos_item["pis_vbc"] = _parse_float(_text(_find(pis_grupo, "nfe:vBC")))
                        impostos_item["pis_ppis"] = _parse_float(_text(_find(pis_grupo, "nfe:pPIS")))
                        impostos_item["pis_vpis"] = _parse_float(_text(_find(pis_grupo, "nfe:vPIS")))
                # COFINS
                if 'COFINS' in imposto_detalhe.tag:
                    cofins_grupo = imposto_detalhe[0] if len(imposto_detalhe) > 0 else None # COFINSAliq, etc.
                    if cofins_grupo is not None:
                        impostos_item["cofins_cst"] = _text(_find(cofins_grupo, "nfe:CST"))
                        impostos_item["cofins_vbc"] = _parse_float(_text(_find(cofins_grupo, "nfe:vBC")))
                        impostos_item["cofins_pcofins"] = _parse_float(_text(_find(cofins_grupo, "nfe:pCOFINS")))
                        impostos_item["cofins_vcofins"] = _parse_float(_text(_find(cofins_grupo, "nfe:vCOFINS")))

        # Combina todos os dados para a linha final
        linha_final = {**dados_comuns, **item_dados, **impostos_item}
        linhas_finais.append(linha_final)
        
    return linhas_finais

