import logging
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from botocore.exceptions import ClientError

class MojoAwsMail:
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

    def send_mail(self, subject, recipients, text=None, html=None):
        # Try to send the email.
        try:
            # Provide the contents of the email.
            message = {
                'Subject': {
                        'Charset': self.charset,
                        'Data': subject}
                }
            body = {}
            if text is not None:
                body['Text'] = {
                    'Charset': self.charset,
                    'Data': text
                }
            if html is not None:
                body['Html'] = {
                    'Charset': self.charset,
                    'Data': html
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
            raise Exception(f"MojoAwsMail : send_mail: {e.response['Error']['Message']}")
        else:
            logging.info("Email sent! Message ID:"),
            logging.info(response['MessageId'])

    def send_raw_email(self, subject, recipients, body=None, attachments=None):
        """
        Sends email with attachments
        :param subject: Subject of the email
        :param recipients: List of recipients
        :param from_name: Name of the sender
        :param body: Body of the email ('\n' are converted to '< br/>')
        :param attachments: List of paths of files to attach
        """

        if attachments is None:
            attachments = []

        if type(recipients) is list:
            recipients = ",".join(recipients)

        message = MIMEMultipart()

        message['Subject'] = subject
        message['To'] = recipients
        if body:
            part = MIMEText(body.replace("\\n", "<br />").replace("\n", "<br />"), "html")
            message.attach(part)

        for attachment in attachments:
            part = MIMEApplication(open(attachment, 'rb').read())
            part.add_header('Content-Disposition', 'attachment', filename=attachment.split("/")[-1])
            message.attach(part)


        self.client.send_raw_email(
            Source=self.sender,
            Destinations=message['To'].split(","),
            RawMessage={
                'Data': message.as_string()
            }
        )

