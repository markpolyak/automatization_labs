import imaplib
import smtplib

from email.header import Header as mkh  # Функция кодирования заголовков для письма
from email.mime.multipart import MIMEMultipart  # Модуль формирования сообщений из нескольких частей
from email.mime.text import MIMEText  # Модуль простого текстового сообщения


class YandexMail:
    IMAP_PORT = "993"
    IMAP_SERVER = "imap.yandex.ru"

    SMTP_PORT = "465"
    SMTP_SERVER = "smtp.yandex.ru"

    @staticmethod
    def get_email_address(login):
        return "{}@yandex.ru".format(login)

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def create_imap_client(self):
        client = imaplib.IMAP4_SSL(YandexMail.IMAP_SERVER, YandexMail.IMAP_PORT)
        client.login(self.login, self.password)
        client.select()  # выбираем папку, по умолчанию - INBOX
        return client

    def create_smpt_client(self):
        return YandexSMTPClient(self.login, self.password)


class YandexSMTPClient:
    def __init__(self, login, password):
        self._login = login
        self._client = smtplib.SMTP_SSL('{0}:{1}'.format(
            YandexMail.SMTP_SERVER, YandexMail.SMTP_PORT))
        self._client.ehlo()
        self._client.login(login, password)

    def send(self, email_to, body,
             subject="Автоматический ответ системы приёма лабораторных работ"):
        email_from = YandexMail.get_email_address(self._login)

        # если надо отправить нескольким адресатам то [adr1,adr2...]
        # объяснение на http://qaru.site/questions/62570/mail-multipartalternative-vs-multipartmixed
        # https://www.programcreek.com/python/example/53141/email.MIMEMultipart.MIMEMultipart
        # http://qaru.site/questions/2280631/how-to-send-a-email-body-part-through-mimemultipart
        message = MIMEMultipart('alternative')
        message['Subject'] = mkh(subject, 'UTF-8')
        message['From'] = email_from
        message['To'] = email_to
        text = body
        html = '<div>' + body + '</div>'

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')  # не будем использовать

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        message.attach(part1)
        message.attach(part2)  # это для HTML не будем использовать

        self._client.sendmail(email_from, email_to, message.as_string())

    def quit(self):
        self._client.quit()
