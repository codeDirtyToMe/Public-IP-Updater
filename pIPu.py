#!/usr/bin/python3.5
"""This is a python only version of my public IP updater script.
Originally, it was this crazy fucking hodgepodge of a shell script that 
made various calls to other python and shell scripts in order to do 
what it does. So, what does it do? Well, it is designed to run as a 
cronjob every... I don't know, 20 minutes? It goes out and grabs the 
public IP from a Google query. It checks this with a value on storage. 
If it's different and matches an IP regex, then it emails the admin the 
updated IP. This is useful if one is running an SSH server and doesn't 
want to get locked out of their server / pay for a static IP. 
Obviously, it is meant to be run from the server itself. This is all 
done in order to prevent DHCP from messing up one's ability to call 
home.

Need to get it working with IPv6 as well as IPv4. That regex will cause 
a bit of a headache.

How to use: ./pIPu -e youremail@gmail.com -p yourhorriblepassword  #Probably want to use a burner.

By, codeDirtyToMe

Consolidation started 9 October 2017: Made a surprising amount of progress. Some regular expressions are
still needed."""

import os, sys, re, argparse, shutil, bs4, requests, smtplib

#Arguments##############################################################################################
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--email", type=str, help="Email address that any IPs will be emailed to.")
parser.add_argument("-p", "--passwd", type=str, help="Passwd for email address.")
arguments = parser.parse_args()

argEmail = arguments.email
argPasswd = arguments.passwd

if argEmail == None or argPasswd == None :
    print("Error: The -e and -p options w/ arguments are not really options, they're more like mandatory.")
    exit(1)

#wimip##################################################################################################
def wimip() :
    #First things first; insert my wimip code and make some minor modifications.
    #url searching for "my ip" on Google assigned to variable.
    retrievedWebPage = requests.get('https://www.google.com/search?q=my+ip&ie=utf-8&oe=utf-8')

    #Create soup object.
    soupWebPage = bs4.BeautifulSoup(retrievedWebPage.text, "html.parser")

    #Extracting division containing public IP from HTML source code.
    HTMLPublicIP = soupWebPage.select('div ._h4c._rGd.vk_h')

    #Extract the IP from the HTML source code.
    currentPublicIP = HTMLPublicIP[0].getText()

    #Return the public IP address.
    publicIP = str(currentPublicIP)
    return publicIP

#Emailer#################################################################################################
def emailer(mailerIP) :
    messageIPchange = """Subject:, Public, IP, address, has, changed.,The, new, IP, address, is: ,"""

    #The following lines are for appending the supplied argument to the email message.
    listMessageIPchange = messageIPchange.split(',') #Create a list from the message.
    listMessageIPchange.insert(6, '\n\n') #Create a newline feed after the subject. Needs two for some damn reason.
    listMessageIPchange.append(mailerIP) #Append the new IP address.
    messageIPchange = ''.join(listMessageIPchange) #Convert back to string.

    #Create regex for testing for HTTP success code.
    httpSuccessRe = re.compile(r'^[2](\d{2})') #Pattern: Three digit number beginning with 2.

    #Create smtp object for gmail SMTP server on port 587. This assumes a gmail account is being used.
    smtpSocket = smtplib.SMTP('smtp.gmail.com', 587)

    #Create list for the .ehlo() call.
    ehloReadOut = list()
    ehloReadOut = smtpSocket.ehlo()

    # Test for Http success code.
    if re.match(httpSuccessRe, str(ehloReadOut[0])) is not None :
        tlsReadOut = list()
        tlsReadOut = smtpSocket.starttls()  # Start SSL encryption.

        # Test for successful Transport Layer Security service start.
        if re.match(httpSuccessRe, str(tlsReadOut[0])) is not None :
            loginReadOut = list()
            # Login to email.
            loginReadOut = smtpSocket.login(argEmail, argPasswd)

            # Test for login success.
            if re.match(httpSuccessRe, str(loginReadOut[0])) is not None :
                # Send email with new IP.
                smtpSocket.sendmail(argEmail, argEmail, messageIPchange)
                smtpSocket.quit()
            else :
                smtpSocket.quit()
                exit(1)
        else :
            smtpSocket.quit()
            exit(1)
    else :
        exit(1)


#main()##################################################################################################
def main() :
    newIP = wimip()  # Web Scraper for public IP

    #Test to see if this program has run before.
    if os.path.isfile(os.getcwd() + "/.currentIPvalue.txt") :
        openFileText = open(".currentIPvalue.txt")
        ipOnStorage = openFileText.read() #Assign value from currentIPvalue.txt to storage variable.
        openFileText.close() #Close it out.

    else : #This would indicate that the program has never run before.
        os.system('touch .currentIPvalue.txt') #Create the currentIPvalue.txt file for permanent storage.
        os.system('chmod 755 .currentIPvalue.txt') #Set up user permissions for the file.
        os.system("echo " + newIP + " > .currentIPvalue.txt") #Write the public IP to file.
        exit(0) #No need to go any further since it's the first time running.

    #I've prepended the currentIPvalue.txt with a '.' in order to keep it somewhat hidden. Although, if
    #an attacker has access to the server the IP is stored on, then the IP is already known to the
    #attacker. Also, need to compare to a regex. Had one written in bash but will have to rewrite in
    #python. Here it is for posterity's sake.
    #IPREGEX=^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$   Hmmm, pretty. Except that it doesn't
    #actually work correctly as values > 254 are accepted. Can't wait to write one for IPv6 :(

    if newIP != ipOnStorage :
        # Overwrite new public IP to storage.
        os.system("echo " + newIP + " > .currentIPvalue.txt")

        #Email the new public IP to the admin.
        emailer(newIP)

    elif newIP == ipOnStorage : #IP hasn't changed, exit till next time.
        exit(0)

    exit(0)

main()
exit(0)
