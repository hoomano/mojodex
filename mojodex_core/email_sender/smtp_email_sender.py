from typing import List
from mojodex_core.email_sender.email_sender import EmailSender
import logging
import configparser
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
from email.mime.image import MIMEImage


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
            if "EMAIL_ADDRESS" not in os.environ:
                raise Exception("EMAIL_ADDRESS is not set")
            if "EMAIL_PASSWORD" not in os.environ:
                raise Exception("EMAIL_PASSWORD is not set")
            if "EMAIL_SENDER_NAME" not in os.environ:
                raise Exception("EMAIL_SENDER_NAME is not set")
            self.smtp_address = os.environ["SMTP_ADDRESS"]
            self.smtp_port = os.environ["SMTP_PORT"]
            self.email_address = os.environ["EMAIL_ADDRESS"]
            self.email_password = os.environ["EMAIL_PASSWORD"]
            self.email_sender_name = os.environ["EMAIL_SENDER_NAME"]
        except Exception as e:
            raise Exception(f"_load_config : {e}")

    def _check_connect_server(self):
        try:
            # we create connexion
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_address, self.smtp_port, context=context) as server:
                # account login
                server.login(self.email_address, self.email_password)
        except Exception as e:
            logging.error(f"_check_connect_server : {e}")

    def send_mail(self, subject: str, recipients: List[str], body: str):
        try:

            # we create an e-mail
            msgRoot = MIMEMultipart("related")
            msgRoot['From'] = self.email_sender_name
            msgRoot['To'] = ", ".join(recipients)
            msgRoot['Subject'] = subject
            msg = MIMEMultipart('alternative')
            msgRoot.attach(msg)

            # Create MIMEText element
            texte_mime = MIMEText(body, 'plain')
            msg.attach(texte_mime)

            # connect
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_address, self.smtp_port, context=context) as server:
                # account login
                server.login(self.email_address, self.email_password)

                # send the email on the existing connection
                server.sendmail(self.email_address, self.email_receivers,
                                msgRoot.as_string())
                # quit the mail server connection
                server.quit()

            return logging.debug("[MojoMail] Email [{}] sent to {}".format(subject, self.email_receivers))

        except Exception as e:
            return logging.error("An error occurred when sending the mail : " + str(e))

    # Set configuration from loader.conf
    def _load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.LOADER_CONF_FILE)
        mail_config_dict = dict(self.config['MAIL_CONFIG'].items())

        for key, value in mail_config_dict.items():
            if key == "email_receivers":
                self.email_receivers = value.split(',')

        try:
            self.email_address = os.environ["EMAIL_ADDRESS"]
            self.email_password = os.environ["EMAIL_PASSWORD"]
            self.smtp_address = os.environ["SMTP_ADDRESS"]
            self.smtp_port = os.environ["SMTP_PORT"]
        except Exception as e:
            return logging.error("An error occurred when sending the mail : {}".format(e) )

