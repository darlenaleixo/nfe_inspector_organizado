# teste_sugestor_tributario.py

from ia_fiscal.sugestor_tributario import SugestorTributario, ContextoOperacao

def testar_sugestor_tributario():
    print("=== TESTE SUGESTOR TRIBUTÁRIO ===\n")
    
    # Inicializa o sugestor
    sugestor = SugestorTributario()
    
    # Contexto de exemplo
    contexto = ContextoOperacao(
        tipo_empresa="comercio",
        regime_tributario="simples",
        uf_origem="SP",
        uf_destino="RJ",
        operacao_tipo="venda",
        valor_operacao=1500.00,
        cliente_tipo="pj"
    )
    
    # Teste 1: Sugestão de NCM
    print("1. SUGESTÃO DE NCM:")
    descricao_produto = "blusa de malha feminina 100% algodão"
    sugestoes_ncm = sugestor.sugerir_ncm(descricao_produto, contexto)
    
    if sugestoes_ncm:
        for i, sugestao in enumerate(sugestoes_ncm, 1):
            print(f"   {i}. {sugestao.codigo} - {sugestao.descricao}")
            print(f"      Confiança: {sugestao.confianca:.1%}")
            print(f"      Razões: {', '.join(sugestao.razoes)}")
            if sugestao.alternativas:
                print(f"      Alternativas: {len(sugestao.alternativas)} opções")
            print()
    else:
        print("   Nenhuma sugestão encontrada\n")
    
    # Teste 2: Sugestão de CFOP
    print("2. SUGESTÃO DE CFOP:")
    sugestoes_cfop = sugestor.sugerir_cfop("venda de mercadoria", contexto)
    
    for i, sugestao in enumerate(sugestoes_cfop, 1):
        print(f"   {i}. {sugestao.codigo} - {sugestao.descricao}")
        print(f"      Confiança: {sugestao.confianca:.1%}")
        print(f"      Razões: {', '.join(sugestao.razoes)}")
        print()
    
    # Teste 3: Sugestão de CST
    print("3. SUGESTÃO DE CST:")
    ncm_escolhido = sugestoes_ncm[0].codigo if sugestoes_ncm else "61046200"
    cfop_escolhido = sugestoes_cfop[0].codigo if sugestoes_cfop else "6101"
    
    sugestoes_cst = sugestor.sugerir_cst(ncm_escolhido, cfop_escolhido, contexto)
    
    for i, sugestao in enumerate(sugestoes_cst, 1):
        print(f"   {i}. {sugestao.codigo} - {sugestao.descricao}")
        print(f"      Confiança: {sugestao.confianca:.1%}")
        print(f"      Razões: {', '.join(sugestao.razoes)}")
        print()
    
    # Teste 4: Aprendizado
    print("4. TESTE DE APRENDIZADO:")
    original = {
        'ncm': '39269090',
        'cfop': '5101', 
        'cst': '00',
        'descricao': 'blusa de malha feminina'
    }
    
    corrigido = {
        'ncm': '61046200',  # NCM correto para blusa de malha
        'cfop': '6101',     # CFOP correto para interestadual
        'cst': '102',       # CST correto para Simples
        'descricao': 'blusa de malha feminina'
    }
    
    print(f"   Original: NCM {original['ncm']}, CFOP {original['cfop']}, CST {original['cst']}")
    print(f"   Corrigido: NCM {corrigido['ncm']}, CFOP {corrigido['cfop']}, CST {corrigido['cst']}")
    
    sugestor.aprender_correcao(original, corrigido, contexto)
    print("   ✅ Aprendizado registrado!")
    
    # Teste 5: Verifica melhoria após aprendizado
    print("\n5. NOVA SUGESTÃO APÓS APRENDIZADO:")
    novas_sugestoes = sugestor.sugerir_ncm("blusa de malha feminina", contexto)
    
    if novas_sugestoes:
        melhor_sugestao = novas_sugestoes[0]
        print(f"   Melhor sugestão: {melhor_sugestao.codigo} - {melhor_sugestao.descricao}")
        print(f"   Confiança: {melhor_sugestao.confianca:.1%}")
        if "anteriormente" in ' '.join(melhor_sugestao.razoes):
            print("   🧠 Sugestão melhorada com aprendizado!")
    
    print("\n✅ Teste do Sugestor Tributário concluído!")

if __name__ == "__main__":
    testar_sugestor_tributario()
