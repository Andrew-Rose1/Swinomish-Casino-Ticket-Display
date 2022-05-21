import requests
from datetime import datetime, timedelta
import json
from email.mime.text import MIMEText
import smtplib
import os
import pyodbc

theseTickets = ""
todaysDate = datetime.now().date()
inactiveDateBound = timedelta(days=14)


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
          "password": "*******"
        }
    print("here")
    token = requests.get("http://10.0.1.4/TrackIt/WebApi/token", data=mydata)
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

def queryOpened(db):
        mycursor = db.cursor()
        sql_tickets = """\
                    SELECT * FROM _SMDBA_._TELMASTE_
                    WHERE STATUS = 'O'
                    ORDER BY SEQUENCE DESC
        """
        mycursor.execute(sql_tickets)
        result = mycursor.fetchall()
        return result

def getName(db, seq):
        mycursor = db.cursor()
        sql_tickets = f"""\
                    SELECT FNAME, NAME FROM _SMDBA_._PERSONNEL_
                    WHERE SEQUENCE = {seq};
        """
        mycursor.execute(sql_tickets)
        result = mycursor.fetchall()
        return result[0][0], result[0][1]

def getNameFromCode(db, code):
        mycursor = db.cursor()
        sql_tickets = f"""\
                    SELECT FNAME, NAME FROM _SMDBA_._PERSONNEL_
                    WHERE CODE = '{code}';
        """
        mycursor.execute(sql_tickets)
        result = mycursor.fetchall()
        return result[0][0], result[0][1]

def gatherTickets(db):
    inactiveTickets = ""
    nowDate = datetime.now().date()
    openTickets = queryOpened(db)
    for ticket in openTickets:
        ticketNumber = ticket[0]
        lastModifiedDateTime = ticket[1]
        lastUser = ticket[2]
        ticketGroup = ticket[3]
        ticketStatus = ticket[8]
        openedDateTime = ticket[12]
        openedSeq = ticket[15]
        closedDateTime = ticket[17]
        ticketSummary = ticket[21]

        if ((ticketGroup == 2 or ticketGroup == 1) and (ticketStatus == "O")):
            lastModified =  lastModifiedDateTime - timedelta(hours=7)
            daysDiff = nowDate - lastModified.date()
            if (daysDiff.days >= inactiveDateBound.days):
                openedFname, openedLname = getName(db, openedSeq)
                lastFname, lastLname = getNameFromCode(db, lastUser)
                inactiveTickets += str(daysDiff.days) + " days -- [#" + str(ticketNumber) + "]: " + ticketSummary + "\n\t Opened by: " + openedFname + " " + openedLname + "\n\t Last edited by: " + lastFname + " " + lastLname + "\n"
    print (inactiveTickets)
    return inactiveTickets


def run():
    f = open("//scripts//outputLog.txt", "a")
    db = pyodbc.connect("Driver=ODBC Driver 18 for SQL Server;Server=10.0.1.4;Database=TRACKIT2020DB;UID=API;PWD=********;PORT=1433;TrustServerCertificate=Yes")
    try:
        inactiveList = gatherTickets(db)

        port = 25  # For starttls
        smtp_server = "internal.swinomishcasino.com"
        sender_email = "dbmail@swinomishcasino.com"
        sender_user = "NLC\dbmail"
        receiver_email = "it@swinomishcasino.com"
        password = "Casino01"

        subject = "[Track-It] Weekly Inactive Ticket Report"
        body = """       --- Track-It! Inactive Tickets ---
--- The following tickets have not been updated in 14 or more days.
--- Please verify that any of these tickets were not mistakenly left open!

{}
    	""".format(inactiveList)

    	# make up message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_user, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        f.write("[Success] -- inactiveCheck.py ran at " + str(datetime.now()) + "\n")
    except Exception as e:
        f.write("[FAILURE] -- inactiveCheck.py tried to run at " + str(datetime.now()) + "\n")
    f.close()

    
run()


