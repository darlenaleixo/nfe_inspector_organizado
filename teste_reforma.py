# teste_reforma.py

from reforma_tributaria.config import ConfigReformaTributaria
from reforma_tributaria.calculadora import CalculadoraReformaTributaria
from reforma_tributaria.validadores import ValidadorReformaTributaria

print("=== TESTE REFORMA TRIBUTÁRIA ===\n")

# Teste 1: Configurações por ano
print("1. Testando configurações por ano:")
config_2025 = ConfigReformaTributaria.get_config_por_ano(2025)
print(f"   2025 - CBS ativo: {config_2025.cbs_ativo} (deve ser False)")

config_2026 = ConfigReformaTributaria.get_config_por_ano(2026)
print(f"   2026 - CBS ativo: {config_2026.cbs_ativo} (deve ser True)")
print(f"   2026 - Alíquota CBS: {config_2026.aliquota_cbs} (deve ser 0.009)\n")

# Teste 2: Calculadora CBS
print("2. Testando calculadora CBS:")
calc = CalculadoraReformaTributaria(config_2026)
resultado_cbs = calc.calcular_cbs(1000.0, {})
print(f"   Produto R$ 1000,00 - CBS: R$ {resultado_cbs['valor']:.2f}")
print(f"   Base de cálculo: R$ {resultado_cbs['base_calculo']:.2f}\n")

# Teste 3: Calculadora IBS
print("3. Testando calculadora IBS:")
resultado_ibs = calc.calcular_ibs(1000.0, {})
print(f"   Produto R$ 1000,00 - IBS: R$ {resultado_ibs['valor']:.2f}\n")

# Teste 4: Compensação 2026
print("4. Testando compensação PIS/COFINS:")
compensacao = calc.calcular_credito_compensacao(
    resultado_cbs['valor'],
    resultado_ibs['valor']
)
print(f"   Total compensável: R$ {compensacao['total_compensavel']:.2f}\n")

# Teste 5: Validador
print("5. Testando validador:")
validador = ValidadorReformaTributaria(config_2026)
dados_item_invalido = {}
erros = validador.validar_grupo_ibs_cbs(dados_item_invalido)
print(f"   Erros encontrados: {len(erros)}")
for erro in erros:
    print(f"   - {erro}")
print("\n✅ SE TODOS OS TESTES PASSARAM, SUA BASE ESTÁ FUNCIONANDO!")
