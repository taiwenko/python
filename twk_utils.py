#!/usr/bin/env python

from datetime import datetime
import smtplib

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

SENDER = 'ironsnail2000@gmail.com'
RECIPIENT = ['twk@google.com', 'haeileen@google.com']

class Twk_utils(object):

	def get_timestamp(self):
		
		dt = datetime.now()
		dt = dt.replace(microsecond=0)
		return str(dt)

	def print_line(self):

		print ' '

	def send_email(self, subject, message=None):
		if message is None:
		    message = subject

		header = ["From: " + SENDER,
		    "Subject: " + subject,
		    "To: " + ','.join(RECIPIENT),
		    "MIME-Version: 1.0",
		    "Content-Type: text/plain"]
		header_str = "\r\n".join(header)	
		session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
		session.ehlo()
		session.starttls()
		session.ehlo()
		session.login('ironsnail2000@gmail.com', 'icharus2000')
		session.sendmail(SENDER, RECIPIENT, header_str + "\r\n\r\n" + message)
		session.quit()

if __name__ == '__main__':
    
    utlis = Twk_utils()
    subject = 'Test Update'
    testing = 'Testing\n'
    utlis.send_email(subject, testing + testing)
    # print utlis.get_timestamp()
    # utlis.print_line()
    # print utlis.get_timestamp()

