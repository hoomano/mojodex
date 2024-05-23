from typing import List
from mojodex_core.email_sender.email_sender import EmailSender
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl


class SMTPEmailSender(EmailSender):


    def __init__(self):
        try:
            self._load_config()
            # Try connection in init to make sure the correct config is user, otherwise, we get an exception
            self._check_connect_server()
        except Exception as e:
            logging.error("Error while initializing the email client : {}".format(e))
            raise e
        
    def _load_config(self):
        try:
            if "SMTP_ADDRESS" not in os.environ:
                raise Exception("SMTP_ADDRESS is not set")
            if "SMTP_PORT" not in os.environ:
                raise Exception("SMTP_PORT is not set")
            if "SENDER_EMAIL" not in os.environ:
                raise Exception("SENDER_EMAIL is not set")
            if "SENDER_PASSWORD" not in os.environ:
                raise Exception("SENDER_PASSWORD is not set")
            if "SENDER_NAME" not in os.environ:
                raise Exception("SENDER_NAME is not set")
            self.smtp_address = os.environ["SMTP_ADDRESS"]
            self.smtp_port = os.environ["SMTP_PORT"]
            self.email_address = os.environ["SENDER_EMAIL"]
            self.email_password = os.environ["SENDER_PASSWORD"]
            self.email_sender_name = os.environ["SENDER_NAME"]
        except Exception as e:
            raise Exception(f"_load_config : {e}")

    def _check_connect_server(self):
        try:
            # we create connexion
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_address, self.smtp_port) as server:
                server.starttls(context=context)
                # account login
                server.login(self.email_address, self.email_password)
        except Exception as e:
            logging.error(f"_check_connect_server : {e}")

    def send_email(self, subject: str, recipients: List[str], text_body: str = None, html_body: str = None):
        try:

            # we create an e-mail
            msgRoot = MIMEMultipart("related")
            msgRoot['From'] = self.email_sender_name
            msgRoot['To'] = ", ".join(recipients)
            msgRoot['Subject'] = subject
            msg = MIMEMultipart('alternative')
            msgRoot.attach(msg)

            # Create MIMEText element
            if text_body is not None:
                # on crée un élément MIMEText
                texte_mime = MIMEText(text_body, 'plain')
                msg.attach(texte_mime)

            if html_body is not None:
                # on créer un élément pour html
                html_mime = MIMEText(html_body, 'html')
                msg.attach(html_mime)


            # connect
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_address, self.smtp_port) as server:
                server.starttls(context=context)
                # account login
                server.login(self.email_address, self.email_password)

                # send the email on the existing connection
                server.sendmail(self.email_address, recipients,
                                msgRoot.as_string())
                # quit the mail server connection
                server.quit()

            logging.info("Email sent!"),

        except Exception as e:
            raise Exception(f"SMTPEmailSender : send_email: {e}")

