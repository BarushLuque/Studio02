import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  

EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

def send_email(to_email, subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        error_msg = "Configuracion de correo incompleta: revisa EMAIL_USER y EMAIL_PASS"
        print(error_msg)
        return False

    try:
        print(f"Intentando conectar a {SMTP_SERVER}:{SMTP_PORT}")
        print(f"Usuario: {EMAIL_USER}")

        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print("Conectado al servidor SMTP")

        server.starttls()
        print("TLS iniciado")

        server.login(EMAIL_USER, EMAIL_PASS)
        print("Login exitoso")

        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()

        print(f"Correo enviado con exito a {to_email}")
        return True
    except Exception as e:
        print(f"Error al enviar correo: {type(e).__name__}: {str(e)}")
        return False
