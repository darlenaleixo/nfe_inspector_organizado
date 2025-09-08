# run_tests.py
from sefaz_integration.client import SefazClient

# Ajuste o caminho e senha do seu PFX
certificado = r"C:\nfe_inspector_organizado\CERT DUDAS REST 2025.pfx"
senha = "1234"

# Instancia o cliente em homologação
client = SefazClient(
    certificado_path=certificado,
    senha_certificado=senha,
    homolog=True
)

# 1) Testar status de serviço
print("=== Status de Serviço ===")
status = client.status_servico()
print(status)

# 2) Testar consulta de NFe (use uma chave de homologação válida ou fake)
print("\n=== Consulta de NFe ===")
chave_teste = "43240714200166000187550010000000091123456789"
resultado = client.consultar_chave(chave_teste)
print(resultado)
