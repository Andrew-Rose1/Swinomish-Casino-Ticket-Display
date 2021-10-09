import requests
from datetime import datetime, timedelta, time
import json
from tkinter import *
import os, os.path
from os import path
import tkinter.font as font
from tkinter.messagebox import showinfo
import ctypes

"""
To Do:
     -- Version 1.4.5
        --- Move firstTicketScan to a serperate function
 -- Allow user to choose sorting method
 -- Outline overdue tickets in red???
 -- Have while loop scan tickets until it recieves an invlad reponse from the next ticket
 -- Implement information bar at bottom of display (time, date, title, open tickets)


Changelog:
 -- Version 1.4.4
    --- Will NOT make API calls between 10:58pm and 11:02pm, because of Shift Report Email that scans att 11pm
 -- Version 1.4.3
    --- Made improvements to ticket range scan. No longer need to define a high and low
 -- Version 1.4.2
    --- Add Information bar on bottom of screen
 -- Version 1.4.1
    --- Add border colors corresponding to time since opened
 -- Version 1.4.0
    --- Changes size of tickets if <= 15 tickets or > 15 tickets

 -- Version 1.3.3
    --- Save bearer token to a txt doc. Upon scan check if bearer token is valid, if not overwrite txt doc with new token
 -- Version 1.3.2
    --- Omitted the display of ticket that start with "WSUS Updates Server Group"
 -- Version 1.3.1
    --- Removed OPened by and Assigned To
    --- Moved COuntdown timer, Sorting method label, and version label behind the tickets
    --- Changed date format to mm-dd-yyyy
    --- Changed sorting method from quickSort to insertion sort
 -- Version 1.3.0
    --- Changed the format to 5x4 to show the top 20 tickets

 -- Version 1.2.2
    --- Moved category under ticket number with smaller text
    --- Added number of notes per ticket
    --- Chnaged background to darker gray, amd ticket color from blue to lighter gray
    --- Slighly increased font
 -- Version 1.2.1
    --- Added sorting method: "Priority, Date Opened"
    --- Added sorting method identifying label
 -- Version 1.2.0
    --- Converted program to object oriented design
    --- Add authorize() and gatherTicket()
    --- Added version label, countdown timer
    --- Changed some fonts

 -- Version 1.0.0
    --- Initial release

 -- Version 0.0.1
    --- Test release
"""


class Window(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.master = master
        self.master.title("Swinomish IT Department Open Tickets")
        self.versionNumber = "1.4.5"

        self.scan = True

        # Define global constants
        self.sortFont = font.Font(size=18, family='Helvetica', weight='bold')
        self.timerFont = font.Font(size=22, family='Helvetica', weight='bold')
        self.versionFont = font.Font(size=9, family='Helvetica')
        self.rootColor = "gray10"
        self.color = "gray25"
        self.openTickets = []

        # Define 15+ ticket's final constants
        self.headerFont = font.Font(size=16, family='Helvetica', weight='bold')
        self.displayNameFont = font.Font(size=13, family='Calibri', weight='bold')
        self.valueFont = font.Font(size=13, family='Calibri')
        self.valueFont2 = font.Font(size=11, family='Calibri')

        # Define <= 15 ticket's final constants
        self.headerFont_XL = font.Font(size=18, family='Helvetica', weight='bold')
        self.displayNameFont_XL = font.Font(size=15, family='Calibri', weight='bold')
        self.valueFont_XL = font.Font(size=15, family='Calibri')
        self.valueFont2_XL = font.Font(size=13, family='Calibri')

        if os.stat("firstScan.txt").st_size == 0:
            self.firstTicket = 1
        else:
            firstScanFile = open("firstScan.txt", "r")
            self.firstTicket = firstScanFile.readline()
            firstScanFile.close()
        self.isFirstValid = True

        self.lowerTime = time(22,58,00)
        self.upperTime = time(23,2,00)

        self.init_window()


    def authorize(self):
        tokenFile = open("authToken.txt", "r")
        bearerToken = tokenFile.read()
        tokenFile.close()
        myHeader = {
          "Authorization": "Bearer " + bearerToken
        }
        return myHeader


    def getNewToken(self):
        mydata = {
          "grant_type": "password",
          "username": "SYSTEM ADMINISTRATION\******",
          "password": "*******"
        }
        token = requests.get("http://10.0.6.8/TrackIt/WebApi/token", data=mydata)
        bearerToken = token.json()["access_token"]
        print("Expires in: " + str(token.json()["expires_in"]) + " days")
        tokenFile = open("authToken.txt", "w")
        tokenFile.write(bearerToken)
        print("Writing a new token at " + str(datetime.now()))
        tokenFile.close()
        myHeader = {
          "Authorization": "Bearer " + bearerToken
        }
        return myHeader


    def gatherTickets(self, myHeader):
        self.openTickets.clear()
        firstInc = int(self.firstTicket)
        notValidCounter = 0
        self.vendorCounter = 0
        self.enduserCounter = 0
        self.pausedCounter = 0
        self.partsCounter = 0
        while (self.scan):
            # CHeck if ticket number in text documnet is open or Closed
            #   If open, continue normally
            #   If Closed, iterate through until you find the first open ticket
            while (self.isFirstValid):
                url = 'http://10.0.6.8/TrackIt/WebApi/tickets/' + str(firstInc)
                firstResponse = requests.get(url, headers=myHeader)
                if firstResponse:
                    firstJSON = firstResponse.json()
                    if (firstJSON["Ticket"]["96"]["Value"] == "Open") or (firstJSON["Ticket"]["96"]["Value"] == "Waiting on Vendor") or (firstJSON["Ticket"]["96"]["Value"] == "Waiting on End User") or (firstJSON["Ticket"]["96"]["Value"] == "Paused") or (firstJSON["Ticket"]["96"]["Value"] == "Parts on Order") or (firstJSON["Ticket"]["96"]["Value"] == "Escalated"):
                        self.isFirstValid = False
                        firstScanFile = open("firstScan.txt", "w")
                        firstScanFile.write(str(firstInc))
                        firstScanFile.close()
                    else:
                        firstInc += 1
                else:
                    firstInc += 1

            url = 'http://10.0.6.8/TrackIt/WebApi/tickets/' + str(firstInc)
            response = requests.get(url, headers=myHeader)
            if response:
                notValidCounter = 0
                ticketJSON = response.json()
                if (ticketJSON["Ticket"]["96"]["Value"] == "Open") and not (ticketJSON["Ticket"]["22"]["Value"].startswith("WSUS Updates Server Group")):
                    url2 = 'http://10.0.6.8/TrackIt/WebApi/tickets/' + str(firstInc) + '/Notes/0/0'
                    response2 = requests.get(url2, headers=myHeader)
                    ticketCountJSON = response2.json()
                    self.openTickets.append(Ticket(ticketJSON, ticketCountJSON["Count"]))
                elif (ticketJSON["Ticket"]["96"]["Value"] == "Waiting on Vendor"):
                    self.vendorCounter += 1
                elif (ticketJSON["Ticket"]["96"]["Value"] == "Waiting on End User"):
                    self.enduserCounter += 1
                elif (ticketJSON["Ticket"]["96"]["Value"] == "Parts on Order"):
                    self.partsCounter += 1
                elif (ticketJSON["Ticket"]["96"]["Value"] == "Paused"):
                    self.pausedCounter += 1
            else:
                notValidCounter += 1
                if notValidCounter >= 20:
                    self.scan = False
            firstInc += 1
        self.scan = True
        self.insertionSort(self.openTickets)


    def insertionSort(self, arr):
        for i in range(1, len(arr)):
            if arr[i].priority != "":
                key = arr[i]
                j = i-1
                if arr[j].priority != "":
                    while j >=0 and int(key.priority) < int(arr[j].priority) :
                            arr[j+1] = arr[j]
                            j -= 1
                    arr[j+1] = key

    def countdown(self, time):
        self.curTimeLabel['text'] = str(datetime.now().time())[:5]
        minutes = time // 60
        seconds = time % 60
        if seconds < 10:
            seconds = "0" + str(seconds)
        self.cdLabel['text'] = "Refreshing in: " + str(minutes) + ":" + str(seconds)

        if time > 0:
            root.after(1000, self.countdown, time-1)
        else:
            self.timeNow = datetime.now().time()
            self.cdLabel['text'] = "Refreshing..."
            if self.timeNow > self.lowerTime and self.timeNow <= self.upperTime:
                self.countdown(300)
            else:
                self.init_window()


    def init_window(self):
        # Authorize and grab open tickets
        try:
            authorizedHeader = self.authorize()
            #test current authorization token
            url = 'http://10.0.6.8/TrackIt/WebApi/tickets/344'
            response = requests.get(url, headers=authorizedHeader)
            if response.status_code != 200:
                authorizedHeader = self.getNewToken()
        except:
            self.countdown(300)
        self.gatherTickets(authorizedHeader)

        # Remove old ticket frames
        for widget in root.winfo_children():
                widget.destroy()

    # Sorting Label
        self.sortLabel = Label(root, text="Sorting method:", fg="white", bg=self.rootColor, justify="right")
        self.sortLabel['font'] = self.sortFont
        self.sortLabel.place(x=1700, y=20)

        self.sortLabel = Label(root, text="Priority, Date Opened", fg="white", bg=self.rootColor, justify="right")
        self.sortLabel['font'] = self.sortFont
        self.sortLabel.place(x=1640, y=52)

    # Countdown Timer
        self.cdLabel = Label(root, fg="white", bg=self.rootColor)
        self.cdLabel['font'] = self.timerFont
        self.cdLabel.place(x=1590, y=1045)

    # Version Label
        self.versionLabel = Label(root, text="V " + self.versionNumber, fg="white", bg=self.rootColor)
        self.versionLabel['font'] = self.versionFont
        self.versionLabel.place(x=1860, y=1060)

    # Open Ticketes
        self.numTicketLabel = Label(root, text=str(len(self.openTickets)) + " Open Tickets", fg="white", bg=self.rootColor)
        self.numTicketLabel['font'] = self.timerFont
        self.numTicketLabel.place(x=870, y=1045)

    # Date
        self.todayDateLabel = Label(root, text=str(datetime.now().today().strftime("%b %d %Y")), fg="white", bg=self.rootColor)
        self.todayDateLabel['font'] = self.valueFont
        self.todayDateLabel.place(x=95, y=1057)

    # Current Time
        self.curTimeLabel = Label(root, fg="white", bg=self.rootColor)
        self.curTimeLabel['font'] = self.timerFont
        self.curTimeLabel.place(x=10, y=1045)

    # Paused Tickets
        self.pausedLabel = Label(root, text="Paused Tickets: " + str(self.pausedCounter), fg="white", bg=self.rootColor)
        self.pausedLabel['font'] = self.sortFont
        self.pausedLabel.place(x=1694, y=865)

    # Waiting on Vendor
        self.vendorLabel = Label(root, text="Waiting on Vendor: " + str(self.vendorCounter), fg="white", bg=self.rootColor)
        self.vendorLabel['font'] = self.sortFont
        self.vendorLabel.place(x=1653, y=905)

    # Waiting on End User
        self.enduserLabel = Label(root, text="Waiting on End User: " + str(self.enduserCounter), fg="white", bg=self.rootColor)
        self.enduserLabel['font'] = self.sortFont
        self.enduserLabel.place(x=1632, y=945)

    # Waiting on Parts
        self.partsLabel = Label(root, text="Waiting on Parts: " + str(self.partsCounter), fg="white", bg=self.rootColor)
        self.partsLabel['font'] = self.sortFont
        self.partsLabel.place(x=1678, y=985)


        rcounter = 0
        ccounter = 0
        if len(self.openTickets) > 15:
            self.colLimit = 3
            for t in self.openTickets:
                if t.priority == "1":
                    pcolor = "red3"
                elif t.priority == "2":
                    pcolor = "darkorange2"
                elif t.priority == "3":
                    pcolor= "yellow2"
                elif t.priority == "4":
                    pcolor= "deepskyblue2"
                elif t.priority == "5":
                    pcolor= self.color
                else:
                    pcolor = self.color

                # Ticket Frame
                rawOpenDate = datetime.strptime(t.open, '%m-%d-%Y')
                if datetime.now() > rawOpenDate + timedelta(days = 12):
                    frame1 = Frame(root,bg=self.color,width=374,height=257,padx=3,pady=3, highlightbackground="red", highlightcolor="red", highlightthickness=3.5, bd=0)
                    frame1.grid(row=rcounter, column=ccounter, padx=5,pady=3)
                elif datetime.now() > rawOpenDate + timedelta(days = 7):
                    frame1 = Frame(root,bg=self.color,width=374,height=257,padx=3,pady=3, highlightbackground="orange", highlightcolor="orange", highlightthickness=2.5, bd=0)
                    frame1.grid(row=rcounter, column=ccounter, padx=5,pady=3)
                else:
                    frame1 = Frame(root,bg=self.color,width=374,height=257,padx=3,pady=3)
                    frame1.grid(row=rcounter, column=ccounter, padx=5,pady=3)

                # Ticket ID Label
                label = Label(frame1, text="Ticket " + t.id, bg=self.color, fg="white")
                label['font'] = self.headerFont
                label.place(x=115,y=1)

                # Category Label
                frame2 = Frame(frame1,bg=self.color,width=150,height=20,padx=1,pady=1)
                frame2.place(x=95, y=28)
                frame2.pack_propagate(False)

                label2 = Label(frame2, text=t.category, wraplength= 250,bg=self.color, fg="white", pady=0)
                label2['font'] = self.versionFont
                label2.pack()

                # Priority Label
                label0 = Label(frame1, text= t.priority, bg=pcolor)
                label0['font'] = self.headerFont
                label0.place(x=5,y=1)

                # Date Label
                label2 = Label(frame1, text="Opened:", wraplength= 250,bg=self.color, fg="white")
                label2['font'] = self.valueFont2
                label2.place(x=295,y=0)

                label0 = Label(frame1, text= t.open, bg=self.color, fg="white")
                label0['font'] = self.valueFont2
                label0.place(x=287,y=19)

                # Summary Label
                label1 = Label(frame1, text="Summary: ",bg=self.color, fg="white", pady=0)
                label1['font'] = self.displayNameFont
                label1.place(x=7,y=48)

                label2 = Label(frame1, text=t.summary,wraplength= 250,bg=self.color, justify="left", fg="white", pady=0)
                label2['font'] = self.valueFont
                label2.place(x=115,y=48)

                # Requestor Label
                label1 = Label(frame1, text="Requested by: ",bg=self.color, fg="white", pady=0)
                label1['font'] = self.displayNameFont
                label1.place(x=7,y=118)

                label2 = Label(frame1, text=t.requestor,bg=self.color, fg="white", pady=0)
                label2.place(x=140,y=118)
                label2['font'] = self.valueFont

                # Info Label
                label1 = Label(frame1, text="Additional Info: ", bg=self.color, fg="white", pady=0)
                label1['font'] = self.displayNameFont
                label1.place(x=7,y=139)

                frame3 = Frame(frame1,bg=self.color,width=350,height=90,padx=1,pady=1)
                frame3.place(x=20, y=160)

                label2 = Label(frame3, text=t.addInfo, wraplength= 340, bg=self.color, justify="left", fg="white", pady=0)
                label2['font'] = self.valueFont2
                label2.pack()

                # Note Count Label
                label1 = Label(frame1, text="Number of Notes:  " + str(t.notes), bg="gray15", fg="white", pady=0)
                label1['font'] = self.valueFont2
                label1.place(x=238,y=232)

                rcounter += 1
                if rcounter > self.colLimit:
                    ccounter +=1
                    rcounter = 0
            self.countdown(300)

        # if less than 16 tickets
        else:
            self.colLimit = 2
            for t in self.openTickets:
                if t.priority == "1":
                    pcolor = "red3"
                elif t.priority == "2":
                    pcolor = "darkorange2"
                elif t.priority == "3":
                    pcolor= "yellow2"
                elif t.priority == "4":
                    pcolor= "deepskyblue2"
                elif t.priority == "5":
                    pcolor= self.color
                else:
                    pcolor = self.color

                # Ticket Frame
                rawOpenDate = datetime.strptime(t.open, '%m-%d-%Y')
                if datetime.now() > rawOpenDate + timedelta(days = 12):
                    frame1 = Frame(root,bg=self.color,width=374,height=345,padx=3,pady=3, highlightbackground="red", highlightcolor="red", highlightthickness=3.5, bd=0)
                    frame1.grid(row=rcounter, column=ccounter, padx=5,pady=3)
                elif datetime.now() > rawOpenDate + timedelta(days = 7):
                    frame1 = Frame(root,bg=self.color,width=374,height=345,padx=3,pady=3, highlightbackground="orange", highlightcolor="orange", highlightthickness=2.5, bd=0)
                    frame1.grid(row=rcounter, column=ccounter, padx=5,pady=3)
                else:
                    frame1 = Frame(root,bg=self.color,width=374,height=345,padx=3,pady=3)
                    frame1.grid(row=rcounter, column=ccounter, padx=5,pady=3)


                # Ticket ID Label
                label = Label(frame1, text="Ticket " + t.id, bg=self.color, fg="white")
                label['font'] = self.headerFont_XL
                label.place(x=105,y=1)

                # Category Label
                frame2 = Frame(frame1,bg=self.color,width=150,height=20,padx=1,pady=1)
                frame2.place(x=95, y=33)
                frame2.pack_propagate(False)

                label2 = Label(frame2, text=t.category, wraplength= 250,bg=self.color, fg="white", pady=0)
                label2['font'] = self.versionFont
                label2.pack()

                # Priority Label
                label0 = Label(frame1, text= t.priority, bg=pcolor)
                label0['font'] = self.headerFont_XL
                label0.place(x=5,y=1)

                # Date Label
                label2 = Label(frame1, text="Opened:", wraplength= 250,bg=self.color, fg="white")
                label2['font'] = self.valueFont2_XL
                label2.place(x=280,y=0)

                label0 = Label(frame1, text= t.open, bg=self.color, fg="white")
                label0['font'] = self.valueFont2_XL
                label0.place(x=263,y=21)

                # Summary Label
                label1 = Label(frame1, text="Summary: ",bg=self.color, fg="white", pady=0)
                label1['font'] = self.displayNameFont_XL
                label1.place(x=7,y=55)

                label2 = Label(frame1, text=t.summary,wraplength= 250,bg=self.color, justify="left", fg="white", pady=0)
                label2['font'] = self.valueFont_XL
                label2.place(x=115,y=55)

                # Requestor Label
                label1 = Label(frame1, text="Requested by: ",bg=self.color, fg="white", pady=0)
                label1['font'] = self.displayNameFont_XL
                label1.place(x=7,y=138)

                label2 = Label(frame1, text=t.requestor,bg=self.color, fg="white", pady=0)
                label2.place(x=140,y=138)
                label2['font'] = self.valueFont_XL

                # Assigned Label
                label1 = Label(frame1, text="Assigned to: ", bg=self.color, fg="white", pady=0)
                label1['font'] = self.displayNameFont_XL
                label1.place(x=7,y=163)

                label2 = Label(frame1, text=t.assigned, bg=self.color, fg="white", pady=0)
                label2.place(x=140,y=163)
                label2['font'] = self.valueFont_XL

                # Info Label
                label1 = Label(frame1, text="Additional Info: ", bg=self.color, fg="white", pady=0)
                label1['font'] = self.displayNameFont_XL
                label1.place(x=7,y=188)

                frame3 = Frame(frame1,bg=self.color,width=350,height=90,padx=1,pady=1)
                frame3.place(x=20, y=213)

                label2 = Label(frame3, text=t.addInfo, wraplength= 330, bg=self.color, justify="left", fg="white", pady=0)
                label2['font'] = self.valueFont_XL
                label2.pack()

                # Note Count Label
                label1 = Label(frame1, text="Number of Notes:  " + str(t.notes), bg="gray15", fg="white", pady=0)
                label1['font'] = self.valueFont2_XL
                label1.place(x=215,y=320)

                rcounter += 1
                if rcounter > self.colLimit:
                    ccounter +=1
                    rcounter = 0
            self.countdown(300)



class Ticket:
    def __init__(self, ticket, count):
        self.notes = count
        try:
            self.id = str(ticket["Ticket"]["1"]["Value"])
        except:
            self.id = "N/A"

        try:
            self.oldOpen = str(ticket["Ticket"]["12"]["Value"])[:10]
            month = self.oldOpen[5:7]
            day = self.oldOpen[8:10]
            year = self.oldOpen[:4]
            self.open = month + "-" + day + "-" + year
        except:
            self.open = "N/A"

        try:
            self.summary = ticket["Ticket"]["22"]["Value"]
        except:
            self.summary = "N/A"

        try:
            self.addInfo = ticket["Ticket"]["7"]["Value"]
        except:
            self.addInfo = "N/A"

        try:
            self.category = ticket["Ticket"]["72"]["Value"]
        except:
            self.category = "N/A"

        try:
            self.priority = str(ticket["Ticket"]["107"]["Value"])[0]
            if self.priority == "H":
                self.priority = "2"
            elif self.priority == "M":
                self.priority = "3"
            elif self.priority == "L":
                self.priority = "4"
        except:
            self.priority = ""

        try:
            self.status = ticket["Ticket"]["96"]["Value"]
        except:
            self.status = "N/A"

        try:
            self.requestor= ticket["Ticket"]["149"]["Value"]
        except:
            self.requestor = "N/A"

        try:
            self.openedBy = ticket["Ticket"]["177"]["Value"]
        except:
            self.openedBy = "N/A"

        try:
            self.assigned = ticket["Ticket"]["157"]["Value"]
        except:
            self.assigned = "N/A"



root = Tk()
root.configure(background="gray10")
root.attributes('-fullscreen', True)
root.resizable(False, False)
root.geometry("1920x1080")
app = Window(root)
root.mainloop()
