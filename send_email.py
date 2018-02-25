from email.mime.text import MIMEText
from datetime import datetime
import smtplib

from_email = "crispycrispycode@gmail.com"
password = "godofthesun3010"


def send_alert(to_email, html_template):
    message = html_template
    msg = MIMEText(message, 'html')
    msg['Subject'] = "Carousell Price Alert"
    msg['To'] = to_email
    msg['From'] = from_email
    gmail = smtplib.SMTP('smtp.gmail.com', 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, password)
    gmail.send_message(msg)
    # log time of price alert
    with open("sent_alerts.txt", "a") as text_file:
        text_file.write(to_email + " " + str(datetime.now()))


def send_confirmation(to_email, html_template):
    message = html_template
    msg = MIMEText(message, 'html')
    msg['Subject'] = "Carousell-Price-Tracker Email Confirmation"
    msg['To'] = to_email
    msg['From'] = from_email
    gmail = smtplib.SMTP('smtp.gmail.com', 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, password)
    gmail.send_message(msg)
