# Swinomish Casino & Lodge IT Department Ticket Display
This was a program created to display our IT Department's open help desk tickets. It uses python and BMC's API for their application, Track-It.
We run this program on a raspberry pi connected to a TV in the IT Department's office.

In addition to the main display board, I have also developed a daily summary report and an inactive ticket scanner. More about these additions below.

Since this software's initial deployment, many departmetns have requested their own version of the Ticket Display Board. I have modified and deployed variations of this software across Swinomish Casino and Lodge.

## Features
- Dynamically change the size of the tickets depending on how many tickets need to be displayed (>15 or <=15).
- Priority and date sorting of open tickets.
- Outline tickets in orange or red based on time since opened.
- Hides tickets tagged as waiting on parts, waiting on vendor, waiting on end user, paused, or any ticket related to a monthly server update group.


## Ticket Display Board

### > 15 Open Tickets
![Full20_TicketDisplay1](https://user-images.githubusercontent.com/55816533/136676440-e7796f44-742f-4a09-b114-e282d81bb50d.jpg)
This is an example of the ticket diplay board when there are more than 15 open tickets to display.

### <= 15 Open Tickets
![LessThan16_TicketDisplay1](https://user-images.githubusercontent.com/55816533/136676443-371f8747-6f92-4ecc-84b3-d3da1ae5b839.jpg)
This is an example of the ticket display board when there are less than 16 open tickets to display.

### About
1. The program will try to use the saved bearer token from the "authToken.txt" file. If API access is granted then continue, if access is denied then reauthorize and save new token to "authToken.txt".
2. Grab the ticket number saved in "firstScan.txt" and check if that ticket is open or closed. If it is open then continue normally. If it is closed then continue to iterate through tickets until you find the next open ticket. Save this ticket number in "firstScan.txt".
3. Scan through tickets starting at "firstScan" up until there are 15 tickets in a row that do not exist. Terminate scan loop after this. All tickets are saved into ticket objects.
4. Now for all gathered tickets simply use tkinter and display them in the desired format.
5. Rescan every 5 minutes. Newly scanned tickets are stored in objects prior to clearing the screen, to ensure minimal downtime of ticket display.

### Pervious Version
Prior to v2.0, this program relied soley on API calls to acquire ticket data. Unfortunately the BMC API is not the fastes thing in the world. I have since rebuilt this program in such a way to utilize both SQL queries and API calls. This makes the rescan of tickets much faster, as I can just query the "open tickets" table, and make API calls on that list. The previous version has been archived in the folder "Older Versions".

## Daily Summary Report
![DailyReportExample1](https://user-images.githubusercontent.com/55816533/136676888-deb78002-13c0-4094-960a-a95fdcb6237c.jpg)

### About
This additional program will send out a daily report of the department's tickets via email.

At 11:00pm this script will run via a cronjob on our department's automation server where it gathers 3 things:
- Today's closed tickets
- Today's new open tickets (opened today, but not yet closed)
- Today's updated tickets (tickets not opened today, but have had notes added to them today)

The script will then format the above information into and email and send it off the the IT Department.

## Inactive Ticket Check
![image](https://user-images.githubusercontent.com/55816533/169634067-365edeac-5ed2-4a85-b4d0-b3e0873d3ebb.png)

### About
This additional program will send out a weekly report of the department's inactive tickets vial email.

A ticket is said to be inactive if it has not had a status change in the past 14 days.
