#!/usr/bin/env python

# import smtplib

# def prompt(prompt):
#     return raw_input(prompt).strip()

# fromaddr = prompt("From: ")
# toaddrs  = prompt("To: ").split()
# print "Enter message, end with ^D (Unix) or ^Z (Windows):"

# # Add the From: and To: headers at the start!
# msg = ("From: %s\r\nTo: %s\r\n\r\n"
#        % (fromaddr, ", ".join(toaddrs)))
# print msg
# while 1:
#     try:
#         line = raw_input()
#     except EOFError:
#         break
#     if not line:
#         break
#     msg = msg + line

# print "Message length is " + repr(len(msg))

# server = smtplib.SMTP('localhost')
# server.set_debuglevel(1)
# server.sendmail(fromaddr, toaddrs, msg)
# server.quit

import smtplib
 
def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com:587'):
    header  = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message
 
    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login,password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()

sendemail(from_addr    = 'ironsnail2000@gmail.com', 
          to_addr_list = ['taiwenko@gmail.com, twk@google.com',],
          cc_addr_list = ['twk@google.com'], 
          subject      = 'Howdy', 
          message      = 'Howdy from a python function\ndo you m', 
          login        = 'ironsnail2000@gmail.com', 
          password     = 'icharus2000')