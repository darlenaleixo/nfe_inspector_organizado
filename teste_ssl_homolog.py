import requests

# URL do WSDL de homologação (SVRS, usado pelo RJ também)
url = "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeConsulta/NFeConsulta4.asmx?WSDL"

# Caminhos absolutos para seus arquivos cert.pem e key.pem
cert_pem = r"C:\nfe_inspector_organizado\CERT\cert.pem"
key_pem  = r"C:\nfe_inspector_organizado\CERT\key.pem"

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
