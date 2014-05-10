__author__ = 'cruor'
from flask.ext.mail import Message
from app import mail
from decorators import async
from app import app
from threading import Thread

@async
def send_async_email(msg):
    with app.app_context():
       mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    rec = []
    rec.append(recipients)
    msg = Message(subject, sender=str(sender), recipients=rec)
    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)


def register_mail(subject, sender, recipient, username, password):
    pass

def receipt_mail(subject, sender, recipient, username, orderref, type, price, duration):
    pass