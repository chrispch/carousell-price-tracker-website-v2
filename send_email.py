from email.mime.text import MIMEText
import smtplib

from_email = "crispycrispycode@gmail.com"
password = "godofthesun3010"

def send_alert(to_email, listing):
    # msg = MIMEText(message, 'html')
    msg['Subject'] = "carousell-price-tracker Price Alert"
    msg['To'] = to_email
    msg['From'] = from_email
    gmail = smtplib.SMTP('smtp.gmail.com', 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, password)
    gmail.send_message(msg)


def send_confirmation(to_email):

    msg = MIMEText(message, 'html')
    msg['Subject'] = "Carousell-price-tracker Email Confirmation"
    msg['To'] = to_email
    msg['From'] = from_email
    gmail = smtplib.SMTP('smtp.gmail.com', 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, password)
    gmail.send_message(msg)
