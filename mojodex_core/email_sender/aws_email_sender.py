import logging
import os
from typing import List

import boto3
from botocore.exceptions import ClientError
from mojodex_core.email_sender.email_sender import EmailSender

class MojoAwsMail(EmailSender):
    def __init__(self, sender_name, sender_email,  region, charset="UTF-8"):
        try:
            logging.basicConfig(level=logging.INFO)

            # Check if the environment variables are set
            if "AWS_ACCESS_KEY_ID" not in os.environ:
                raise Exception("AWS_ACCESS_KEY_ID is not set")
            if "AWS_SECRET_ACCESS_KEY" not in os.environ:
                raise Exception("AWS_SECRET_ACCESS_KEY is not set")
            self.sender = f"{sender_name} <{sender_email}>"
            self.region = region
            self.charset = charset
            self.client = boto3.client('ses', region_name=self.region)
            # configure login
            # use iam called mojo-monitoring
            # https://docs.aws.amazon.com/ses/latest/DeveloperGuide/setting-up-ses.html
            # https://docs.aws.amazon.com/ses/latest/DeveloperGuide/using-iam.html
        except Exception as e:
            raise Exception(
                "MojoAwsMail : Error while initializing MojoAwsMail : {}".format(e))

    def send_mail(self, subject: str, recipients: List[str], body: str):
        # Try to send the email.
        try:
            # Provide the contents of the email.
            message = {
                'Subject': {
                        'Charset': self.charset,
                        'Data': subject
                        },
                'Body':  {
                        'Text': {
                            'Charset': self.charset,
                            'Data': body
                            },
                        } 
                    }

            response = self.client.send_email(
                Destination={
                    'ToAddresses': recipients
                },
                Message=message,
                Source=self.sender,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            raise Exception(f"MojoAwsMail : send_mail: {e.response['Error']['Message']}")
        else:
            logging.info("Email sent! Message ID:"),
            logging.info(response['MessageId'])
