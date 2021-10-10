import requests
from datetime import datetime, timedelta
import json
from email.mime.text import MIMEText
import smtplib

theseTickets = ""

def authorize():
    tokenFile = open("/scripts/authToken.txt", "r")
    bearerToken = tokenFile.read()
    tokenFile.close()
    myHeader = {
      "Authorization": "Bearer " + bearerToken
    }
    return myHeader

def getNewToken():
    mydata = {
      "grant_type": "password",
      "username": "SYSTEM ADMINISTRATION\******",
      "password": "******"
    }
    token = requests.get("http://10.0.6.8/TrackIt/WebApi/token", data=mydata)
    bearerToken = token.json()["access_token"]
    print("Expires in: " + str(token.json()["expires_in"]))
    tokenFile = open("/scripts/authToken.txt", "w")
    tokenFile.write(bearerToken)
    print("Writing a new token at " + str(datetime.now()))
    tokenFile.close()
    myHeader = {
      "Authorization": "Bearer " + bearerToken
    }
    return myHeader

def gatherTickets(myHeader):
    closedToday = ""
    openedToday = ""
    updatedToday = ""
    notValidCounter = 0
    i = 400
    scan = True
    while (scan):
        url = 'http://10.0.6.8/TrackIt/WebApi/tickets/' + str(i)
        response = requests.get(url, headers=myHeader)
        if response:
            notValidCounter = 0
            ticketJSON = response.json()
            # Closed tickets today
            if ticketJSON["Ticket"]["96"]["Value"] == "Closed" or ticketJSON["Ticket"]["96"]["Value"] == "Completed":
                closeDate = datetime.strptime(ticketJSON["Ticket"]["18"]["Value"][:19], '%Y-%m-%dT%H:%M:%S') - timedelta(hours=7)
                if closeDate.date() == datetime.now().date():
                    closedToday += "[" + str(closeDate)[11:16] + "] -- #" + str(ticketJSON["Ticket"]["1"]["Value"]) + ":   " + ticketJSON["Ticket"]["22"]["Value"] + "\n"
            # New opened tickets today
            elif (datetime.strptime(ticketJSON["Ticket"]["12"]["Value"][:19], '%Y-%m-%dT%H:%M:%S')-timedelta(hours=7)).date() == datetime.now().date():
                openDatetime = datetime.strptime(ticketJSON["Ticket"]["12"]["Value"][:19], '%Y-%m-%dT%H:%M:%S') - timedelta(hours=7)
                openedToday += "[" + str(openDatetime)[11:16] + "] -- #" + str(ticketJSON["Ticket"]["1"]["Value"]) + ":   " + ticketJSON["Ticket"]["22"]["Value"] + "\n"
            # open tickets updated today
            elif (datetime.strptime(ticketJSON["Ticket"]["2"]["Value"][:19], '%Y-%m-%dT%H:%M:%S')- timedelta(hours=7)).date() == datetime.now().date():
                updatedDatetime = datetime.strptime(ticketJSON["Ticket"]["2"]["Value"][:19], '%Y-%m-%dT%H:%M:%S') - timedelta(hours=7)
                updatedToday += "[" + str(updatedDatetime)[11:16] + "] -- #" + str(ticketJSON["Ticket"]["1"]["Value"]) + ":   " + ticketJSON["Ticket"]["22"]["Value"] + "\n"
        else:
            notValidCounter += 1
            if notValidCounter >= 20:
                scan = False
        i += 1

    return closedToday, openedToday, updatedToday


def run():
    f = open("//scripts//outputLog.txt", "a")
    try:
        authorizedHeader = authorize()
        url = 'http://10.0.6.8/TrackIt/WebApi/tickets/480'
        response = requests.get(url, headers=authorizedHeader)
        if response.status_code != 200:
            authorizedHeader = getNewToken()
        closedToday, openedToday, updatedToday = gatherTickets(authorizedHeader)

        port = 25
        smtp_server = "**********"
        sender_email = "**********"
        sender_user = "**********"
        receiver_email = "**********"
        password = "**********"

        subject = "[Track-It] Daily Summary Report for (" + str(datetime.now().strftime('%m/%d/%Y')) + ")"
        body = """
    --- Track-It! Daily Report for {} ---


--- Today's closed tickets:
{}
--- Today's new open tickets:
{}
--- Today's updated tickets:
{}
    	""".format(str(datetime.now().strftime('%m/%d/%Y')), closedToday, openedToday, updatedToday)

    	# make up message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("Attempting to login...")
            server.login(sender_user, password)
            print("Logged In!")
            server.sendmail(sender_email, receiver_email, msg.as_string())

        print("Email sent!")
        f.write("[Success] -- sendDailyReport.py ran at " + str(datetime.now()) + "\n")
    except:
        print("failure")
        f.write("[FAILURE] -- sendDailyReport.py tried to run at " + str(datetime.now()) + "\n")
    f.close()

run()
