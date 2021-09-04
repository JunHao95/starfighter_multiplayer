# gclient.py
# Author: Andrew Smith
# Date: June 2021
# Client side of game application

import socket
import threading
import time 
import pickle

serverTerminationMsg = "TERMINATESERVER1979," # Server Termination method
serverConnectionMsg = "CONNECTTOSERVER1979," # Server Connection String

serverAddressPort   = ("127.0.0.1", 20001)
bufferSize          = 1024

messageHistory = ' ' # Stores Message history from server

class Customer:
    def __init__(self, titleIn, surnameIn, firstnameIn, idNoIn):
        self.title = titleIn
        self.surname = surnameIn
        self.firstname = firstnameIn
        self.idNo = idNoIn
        
    def printCustomer():
        print(self.title)
        print(self.surname)
        print(self.firstname)
        print(self.idNo)
        
# Get's the current date and time and returns in UK format
# Used on both client and server side (date and time logging)
def getUKDateTime():
    # Get current date and time
    ukdatetime = str(datetime.now())
    
    # Break date and time into seperate strings
    splitdatetime = ukdatetime.split()
    
    # Get date part of the string
    datepart = splitdatetime[0]
    
    # Get the time part of the string
    timepart = splitdatetime[1]
    
    # Split the date up into parts
    splitdate = datepart.split("-")
    # Get each date attribute
    dtYear = splitdate[0]
    dtMonth = splitdate[1]
    dtDay = splitdate[2]
    
    # Split the time up into parts
    splittime = timepart.split(":")
    # Get hour and minute
    tHour = splittime[0]
    tMinute = splittime[1]
    
    # Construct string to return
    retString = (dtDay + '-' + dtMonth + '-' + dtYear + ' ' + tHour + ':' + tMinute)
    
    # Return the overall string
    return retString


# Get the Client IP address 
def getClientIPAddress():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    thisClientIP = s.getsockname()[0]
    s.close()
    
    return thisClientIP

# Take in user input to determine action request to server 
def processUserInterfaceRequest():
    global messageHistory
    endLoop = False
    
    
    
    while endLoop == False:    
    
        print(messageHistory)
        
        print("1. Send Connection Request")
        print("2. Terminate Connection to Server")
        print("3. Transmit Data")
        print("4. Exit")
    
        userchoice = input("Enter Choice: ")
    
        if userchoice == '1':
            formulateRequest(1)
            time.sleep(1)
        elif userchoice == '2':
            formulateRequest(2)
            time.sleep(1)
        elif userchoice == '3':
            formulateRequest(3)
            time.sleep(1)
        elif userchoice == '4':
            endLoop = True # Terminate the program

# This function is used to formulate a request
def formulateRequest(RequestTypeIn):
    global serverConnectionMsg
    global serverTerminationMsg
    
    HEADERSIZE = 10
    
    # Create some customer objects
    
    customer1 = Customer('MR', 'SMITH', 'ANDREW', 1)
    customer2 = Customer('MR', 'GISMO', 'BEN', 2)
    customer3 = Customer('MR', 'JENKINS', 'DAVE', 3)
    
    customerCollection = []
    customerCollection.append(customer1)
    customerCollection.append(customer2)
    customerCollection.append(customer3)
    
    msgData = pickle.dumps(customerCollection)
    
    clientRequest = ' '    
    
    if RequestTypeIn == 1:
        # Form Connection Request
        clientRequest = (serverConnectionMsg + str(getClientIPAddress()) + ',' + '20002')
        encodedClientRequest = str.encode(clientRequest)
        sendRequestToServer(encodedClientRequest)
    if RequestTypeIn == 2:
        # Form Termination Request
        clientRequest = (serverTerminationMsg + str(getClientIPAddress()))
        encodedClientRequest = str.encode(clientRequest)
        sendRequestToServer(encodedClientRequest)
    if RequestTypeIn == 3: 
        # Form data send request
        introMsg = 'GAMEDATA,'
        byteIntro = str.encode(introMsg)
        totalmsg = (byteIntro + msgData)
        totalmsg = bytes(f'{len(totalmsg):<{HEADERSIZE}}', "utf-8") + totalmsg
        sendRequestToServer(totalmsg)
        

# This function is used to setup a client communication point
def clientEndPoint():
    global messageHistory
    bufferSize = 1024
    clientPort = 20002
    clientAddress = getClientIPAddress()
    clientAddressPort = ([clientAddress, clientPort])
    
    # Create a datagram socket

    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) 

    # Bind to address and ip

    UDPClientSocket.bind(('127.0.0.1', clientPort)) 

    print("UDP client server up and listening") 
    
    # Listen for incoming datagrams

    while(True):

        bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)

        message = bytesAddressPair[0]

        address = bytesAddressPair[1]

        #serverMsg = "Message from Server:{}".format(message)
        serverMsg = str(message, "utf-8")
        messageHistory = serverMsg
        #serverIP  = "Server IP Address:{}".format(address)
        #serverIP = str(address, "utf-8")
    
        #print(serverMsg)
        #print(serverIP)        
    
    
    

# A function that will send a request to the server 
def sendRequestToServer(RequestToServerIn):
    global serverAddressPort
    global bufferSize

    # Change 
    
    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Send to server using created UDP socket
    UDPClientSocket.sendto(RequestToServerIn, serverAddressPort) 

    # Get message from server
    #msgFromServer = UDPClientSocket.recvfrom(bufferSize)    
    #msg = "Message from Server {}".format(msgFromServer[0])

    # Output message from server 
    #print(msg)
    
    

threadedClientProcess = threading.Thread(target=clientEndPoint)
threadedClientProcess.start()