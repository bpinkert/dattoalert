#!/usr/bin/env python
# Authored by Benjamin Pinkert

import xml.etree.ElementTree as ET 
import requests 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys 
import os

configdict = {} # email configuration
maindict = {} # server backup status
hostlist = [] # used to store appliance host names
input = input #declare input before checking python version
xmlpath = os.path.dirname(os.path.realpath(__file__)) + '/dattoconfig.xml' # path of config file

# uses raw_input if python 2.7.
if sys.version_info[0] == 2:
    input = raw_input

def configureemail():
    """
    configureemail asks the user for the information needed to create the configuration xml file,
    which is used when the script is ran normally.
    """
    # XML structure
    top = ET.Element('config')
    apikey = ET.SubElement(top, 'apikey')
    subject = ET.SubElement(top, 'subject')
    fromaddress = ET.SubElement(top, 'from')
    toaddress = ET.SubElement(top, 'to')
    smtpaddress = ET.SubElement(top, 'smtpserver')

    # prompts for input, then saves as XML
    apikey.text = input("Please enter your Datto API key:   ")
    subject.text = input("Enter the subject used for the email:   ")
    fromaddress.text = input("Enter the from email address:   ")
    toaddress.text = input("Enter the to email address:   ")
    smtpaddress.text = input("Enter the smtp server address:   ")
    ET.ElementTree(top).write(xmlpath)

def pullconfig():
    """
    pullconfig pulls the email parameters in from the dattoemail.xml file. If an IOError is thrown,
    it tells the user to run -config to generate the configuration file.
    """
    # attempt to parse XML file and notify user if file doesn't exist.
    try:
        tree = ET.parse(xmlpath)
    except IOError as err:
        print(err, "\nPlease run dattoemail.py -config to create configuration file.")
        sys.exit(1)
    # creates a configuration dictionary for use with  email module.
    root = tree.getroot()
    for child in root:
        configdict[child.tag] = child.text

def dattopull(apikey):
    """
    dattopull gathers the data from Datto's XML API and populates the hostlist list and maindict dictionary.
    :param apikey:
    """
    apiurl = 'https://device.dattobackup.com/integrateXML.php?feed=xmlstatus&apiKey=' + apikey
    htmlrequest = requests.get(apiurl)
    root = ET.fromstring(htmlrequest.text)
    # Finds all the Datto appliances
    devices = root.findall('./Device')

    # loop through each appliance and finds configured agents
    for hosts in devices:
        protectedsystems = hosts.findall('./protectedMachines/protected')
        lista = []
        for system in protectedsystems:
            servername = system.find('./protectedHostname')
            laststatus = system.find('./lastSnapshot')
            lasttime = system.find('./lastSnapshotTime')
            lista.append([servername.text, laststatus.text, lasttime.text])
        hostname = hosts.find('./hostname')
        hostlist.append(hostname.text)
        maindict[hostname.text] = lista

def email(subject, fromaddress, toaddress, smtphost):
    """
    Generates the email in html and sends it to the recipient address.
    :param subject: email subject
    :param fromaddress: email from address
    :param toaddress: email recipient's address
    :param smtphost: server used to relay the email
    """
    # formatting the email in html.
    dailyemailhtml = "<html><head></head><body>"
    # loops through each device listed and generates the body of the email.
    for hosts in hostlist:
        emailbodyhtlm = "<table border=\"0\" width=\"600\">\n"
        emailbodyhtml = emailbodyhtlm + "<tr><td>" + hosts + ":</td></tr><tr></tr></td></tr><tr></tr></td></tr><tr></tr>\n"
        emailbodyhtml = emailbodyhtml + "<tr><td width=\"30%\">Server Name</td><td width=\"30%\">Status</td><td width=\"30%\">Last Snapshot</td></tr>\n"
        # loops through each server and generates the html for the email.
        for server in maindict[hosts]:
            emailbodyhtml = emailbodyhtml + "<tr><td>" + server[0] + "</td><td>" + server[1]+ "</td><td>" + server[2] + "</td></tr>\n"

        # table closing tags for the email body.
        emailbodyhtml = emailbodyhtml + "<tr></tr><tr></tr></td></tr><tr></tr></td></tr><tr></tr></table>\n\n"
        dailyemailhtml = dailyemailhtml + emailbodyhtml + "\n\n"

    # add some CSS before closing the body
    #dailyemailhtml = dailyemailhtml + "<style type='text/css'> </style>"

    # closing tags for the email.
    dailyemailhtml = dailyemailhtml + "</body></html>"

    # generates the email be sent via smtplib module.
    part2 = MIMEText(dailyemailhtml, 'html')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = fromaddress
    msg['To'] = toaddress
    msg.attach(part2)
    smtpserver = smtplib.SMTP(smtphost)
    smtpserver.sendmail(fromaddress, toaddress, msg.as_string())
    smtpserver.quit()

def main():
    args = sys.argv[-1] # check if config file is present

    if not args or 'dattoemail.py' in args:
        pullconfig()
        dattopull(configdict['apikey'])
        email(configdict['subject'],configdict['from'],configdict['to'],configdict['smtpserver'])
        sys.exit(0)
    if '-config' in args:
        configureemail()
        sys.exit(0)
    print('usage to send email: dattoemail.py')
    print('usage to configure: dattoemail.py -configure')
    sys.exit(1)

if __name__ == '__main__':
    main()
