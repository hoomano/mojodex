import logging
import os
from typing import List

import boto3
from botocore.exceptions import ClientError
from mojodex_core.email_sender.email_sender import EmailSender

class MojoAwsMail(EmailSender):
    def __init__(self, charset="UTF-8"):
        try:
            logging.basicConfig(level=logging.INFO)

            self._load_config()
            
            self.charset = charset
            self.client = boto3.client('ses', region_name=self.region)
            # configure login
            # use iam called mojo-monitoring
            # https://docs.aws.amazon.com/ses/latest/DeveloperGuide/setting-up-ses.html
            # https://docs.aws.amazon.com/ses/latest/DeveloperGuide/using-iam.html
        except Exception as e:
            raise Exception(
                "MojoAwsMail : Error while initializing MojoAwsMail : {}".format(e))
        
    def _load_config(self):
        try:
            if "AWS_ACCESS_KEY_ID" not in os.environ:
                raise Exception("AWS_ACCESS_KEY_ID is not set")
            if "AWS_SECRET_ACCESS_KEY" not in os.environ:
                raise Exception("AWS_SECRET_ACCESS_KEY is not set")
            if "AWS_SES_REGION" not in os.environ:
                raise Exception("AWS_SES_REGION is not set")
            if "SENDER_EMAIL" not in os.environ:
                raise Exception("SENDER_EMAIL is not set")
            if "SENDER_NAME" not in os.environ:
                raise Exception("SENDER_NAME is not set")
            
            self.region = os.environ["AWS_SES_REGION"]
            self.email_address = os.environ["SENDER_EMAIL"]
            self.email_sender_name = os.environ["SENDER_NAME"]
            self.sender = f"{self.email_sender_name} <{self.email_address}>"
        except Exception as e:
            raise Exception(f"_load_config : {e}")

    def send_email(self, subject: str, recipients: List[str], text_body: str = None, html_body: str = None):
        # Try to send the email.
        try:# Provide the contents of the email.
            message = {
                'Subject': {
                        'Charset': self.charset,
                        'Data': subject}
                }
            body = {}
            if text_body is not None:
                body['Text'] = {
                    'Charset': self.charset,
                    'Data': text_body
                }
            if html_body is not None:
                body['Html'] = {
                    'Charset': self.charset,
                    'Data': html_body
                }
            message['Body'] = body

            response = self.client.send_email(
                Destination={
                    'ToAddresses': recipients
                },
                Message=message,
                Source=self.sender,
            )
            
        # Display an error if something goes wrong.
        except ClientError as e:
            raise Exception(f"MojoAwsMail : send_email: {e.response['Error']['Message']}")
        else:
            logging.info("Email sent! Message ID:"),
            logging.info(response['MessageId'])
