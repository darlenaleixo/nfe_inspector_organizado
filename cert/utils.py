import smtplib
from email.message import EmailMessage
from cert.config import NOTIFY_EMAIL

def send_email_alert(days_left):
    msg = EmailMessage()
    msg["Subject"] = f"Alerta: Certificado vence em {days_left} dias"
    msg["From"] = NOTIFY_EMAIL
    msg["To"] = NOTIFY_EMAIL
    msg.set_content(f"Seu certificado digital expira em {days_left} dias.\nRenove-o antes da data de expiração.")

    # Configurar SMTP conforme ambiente
    with smtplib.SMTP("smtp.exemplo.com", 587) as server:
        server.starttls()
        server.login("usuario", "senha")
        server.send_message(msg)
