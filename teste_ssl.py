import requests

# URL do WSDL de consulta da SEFAZ RJ
url = "https://nfe.fazenda.rj.gov.br/NFeConsulta/NFeConsulta4.asmx?WSDL"

# Caminho absoluto para seus arquivos
cert_pem = r"C:\nfe_inspector_organizado\cert\cert.pem"
key_pem = r"C:\nfe_inspector_organizado\cert\key.pem"

try:
    print(f"Tentando conexão com {url} ...")
    response = requests.get(url, cert=(cert_pem, key_pem), verify=True, timeout=30)

    print("✅ Conexão estabelecida!")
    print("Status HTTP:", response.status_code)
    print("Início do conteúdo retornado:\n")
    print(response.text[:500])  # Mostra só os primeiros 500 caracteres do XML

except requests.exceptions.SSLError as e:
    print("❌ Erro de SSL:", e)
except requests.exceptions.ConnectionError as e:
    print("❌ Erro de conexão:", e)
except Exception as e:
    print("❌ Erro inesperado:", e)
