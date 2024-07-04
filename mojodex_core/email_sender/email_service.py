

import os
from mojodex_core.email_sender.email_sender import EmailSender
from mojodex_core.logging_handler import MojodexCoreLogger


class EmailService:  # Singleton
    _instance = None

    admin_email_receivers = os.environ["ADMIN_EMAIL_RECEIVERS"].split(",") if "ADMIN_EMAIL_RECEIVERS" in os.environ else []
    technical_email_receivers = os.environ["TECHNICAL_EMAIL_RECEIVERS"].split(",") if "TECHNICAL_EMAIL_RECEIVERS" in os.environ else []


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmailService, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self.email_service_logger = MojodexCoreLogger("email_service_logger")
        try:
            self._email_sender: EmailSender = self._configure_email_sender()
        except Exception as e:
            self.email_service_logger.error(f"Error initializing email service :: {e}")


    @property
    def configured(self):
        return self._email_sender is not None

    def _configure_email_sender(self):
        try:
            mail_sender = None
            if os.environ.get('AWS_SES_REGION', ''):
                from mojodex_core.email_sender.aws_email_sender import MojoAwsMail
                mail_sender = MojoAwsMail()
                self.email_service_logger.info("AWS SES email client configured.")
            elif os.environ.get('SMTP_ADDRESS', ''):
                from mojodex_core.email_sender.smtp_email_sender import SMTPEmailSender
                mail_sender = SMTPEmailSender()
                self.email_service_logger.info("SMTP email client configured.")
            else:
                self.email_service_logger.warning("No email client configured.")
            return mail_sender
        except Exception as e:
            raise Exception(f"_configure_email_sender: {e}")
        
    def send(self, subject, recipients, text=None, html_body=None):
        try:
            self._email_sender.send_email(subject=subject, recipients=recipients, text_body=text, html_body=html_body)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: send :: {e}")

    def send_technical_error_email(self, error_message):
        try:
            if self.configured:
                self.send(subject=f"MOJODEX ERROR - {os.environ['ENVIRONMENT']}",
                                            recipients=self.technical_email_receivers,
                                            text=error_message)
            else:
                self.email_service_logger.info(f"No email client configured - email to send was tech error: {error_message}")
        except Exception as e:
            self.email_service_logger.error(f"{self.__class__.__name__} :: send_technical_error_email : {e}")


    def send_admin_email(self, subject, text):
        try:
            if self.configured:
                self.send(subject=subject, recipients=self.admin_email_receivers, text=text)
            else:
                self.email_service_logger.info(f"No email client configured - email to send was admin info: {text}")
        except Exception as e:
            self.email_service_logger.error(f"{self.__class__.__name__} :: send_admin_email :: {e}")