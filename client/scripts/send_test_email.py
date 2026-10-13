import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# ---------- CONFIG EMAIL ----------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Charger le fichier .env
load_dotenv()

# Récupérer les variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def send_email(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()

        print("📧 Email sent successfully!")

    except Exception as e:
        print("❌ Failed to send email:", e)

# ----------- TEST -----------
if __name__ == "__main__":
    send_email(
        subject="Test d’envoi d’email (Fog Node)",
        message="Ceci est un email de test envoyé depuis Python. 👍"
    )
