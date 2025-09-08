# test_cert.py
import os
from sefaz_integration.auth import CertificateManager

def test_certificate():
    # Substitua pelos caminhos corretos do seu certificado .pfx e senha
    pfx_path = r"C:\nfe_inspector_organizado\CERT DUDAS REST 2025.pfx"
    password = "1234"

    print("🔍 Testando extração de certificado...")

    # Verifica se o arquivo existe
    if not os.path.exists(pfx_path):
        print(f"❌ Arquivo não encontrado: {pfx_path}")
        return False

    try:
        # Extrai cert e key
        cert_manager = CertificateManager(pfx_path, password)
        cert_file, key_file = cert_manager.get_cert_files()

        # Verifica se os arquivos temporários foram criados
        if os.path.exists(cert_file) and os.path.exists(key_file):
            print(f"✅ Certificado extraído: {cert_file}")
            print(f"✅ Chave privada extraída: {key_file}")
            return True
        else:
            print("❌ Falha na criação dos arquivos temporários")
            return False

    except Exception as e:
        print(f"❌ Erro ao extrair certificado: {e}")
        return False

if __name__ == "__main__":
    success = test_certificate()
    if success:
        print("🎉 Teste de certificado PASSOU!")
    else:
        print("❌ Teste de certificado FALHOU.")
