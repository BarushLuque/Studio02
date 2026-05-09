import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  

EMAIL_USER = "esteticastudio02@gmail.com"
EMAIL_PASS = "wivf trjm zwya wfik"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

print(EMAIL_USER, EMAIL_PASS)

def send_email(to_email, subject, body):
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Servidor smtp
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()

        print("Correo enviado con eexito a", to_email)
        return True
    except Exception as e:
        print("Error al enviar correo:", e)
        return False
