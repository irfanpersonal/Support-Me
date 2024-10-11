# To send an email using the "sendgrid" API in our Python Application we first have to install the 
# third party package called "sendgrid". Once successfully installed you want to load in the following
# three things: os, SendGridAPIClient, and Mail. 

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Next we need to do pass in our API Key so that we can start working with the API. 
sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

# Lastly we will define a function that makes the process of sending an email super easy. All you have to 
# do is pass in a dictionary that provides the from_email, to_emails, subject, and html_content keys/value
# pairs. And internally we will use that to construct the actual "Mail" object. And then using that Mail
# object we pass it into the send mehtod to do the actual sending. At the end it will return the response 
# or result of sending the email. 

from typing import TypedDict

# Create a custom type called "MailDictionary" by inheriting from the class "TypedDict" from the "typing"
# built in package. So whatever we set inside of it must be provided when passing in values for this type
class MailDictionary(TypedDict):
    to_emails: str
    subject: str
    html_content: str

def sendEmail(data: MailDictionary):
    try:
        message = Mail(
            from_email = Email(os.getenv('SENDGRID_VERIFIED_SENDER')),
            to_emails = To(data.get('to_emails')),
            subject = data.get('subject'),
            html_content = Content('text/html', data.get('html_content'))
        )
        response = sg.send(message)
        return response
    except Exception as error:
        print(f"Error: {error}")
        # print("Something went wrong, when trying to send an email!")