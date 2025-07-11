import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

msg = EmailMessage()
msg['Subject'] = "SMTP Test"
msg['From'] = os.getenv("EMAIL_ADDRESS")
msg['To'] = os.getenv("TO_EMAIL")
msg.set_content("This is a test email from SMTP setup.")

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        smtp.send_message(msg)
        print("✅ Test email sent!")
except Exception as e:
    print(f"❌ Failed to send test email: {e}")
