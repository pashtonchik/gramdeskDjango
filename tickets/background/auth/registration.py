from celery import Celery
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, formataddr

from celery import shared_task
import pyotp
from datetime import datetime


@shared_task()
def send_email_code_for_registration(email):
    from backend.models import User, DualFactorRequest

    user = User.objects.get(my_email=email)

    timestamp = int(datetime.now().timestamp())

    dualReq = DualFactorRequest(
        factor_type='email_auth',
        user=user,
        timestamp=timestamp,
        otp=pyotp.HOTP(pyotp.random_base32()).at(timestamp),
        action='registration'
    )
    dualReq.save()
    msg = MIMEMultipart()
    message1 = "Ваш код подтверждения:"
    message = f"<html><body><b><h1>{dualReq.otp}</h1></b></body></html>"
    # setup the parameters of the message
    password = 'dsxf nsga rzte oqhp'
    msg['Message-ID'] = make_msgid()
    msg['From'] = formataddr(("OTP Code Manager", "pashkakakashka9111@gmail.com"))
    msg['To'] = f"{email}"
    msg['Subject'] = "Подтверждение электронной почты."
    msg.set_charset('utf-8')
    # add in the message body
    msg.attach(MIMEText(message1, 'plain'))
    msg.attach(MIMEText(message, 'html'))
    # create server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo('Gmail')
    server.starttls()
    # Login Credentials for sending the mail
    server.login("pashkakakashka9111@gmail.com", password)
    # send the message via the server.
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    print("successfully sent email to %s:" % (msg['To']))