import requests

url = "https://nfe.fazenda.rj.gov.br/NFeConsulta/NFeConsulta4.asmx?WSDL"
cert = ("cert.pem", "key.pem")

try:
    r = requests.get(url, cert=cert, verify=True)
    print("Status:", r.status_code)
    print(r.text[:400])  # mostra só o início do XML
except Exception as e:
    print("Erro:", e)
