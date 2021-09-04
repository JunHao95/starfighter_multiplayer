# gserver.py
# Author: Andrew Smith
# Date June 1st 2021
# Description: Server component for Star-Fighter game

import socket 
import threading
from datetime import datetime
import pickle

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

# A function used to get server IP address (on server side)
def getServerIPAddress():
    # Get the server IP address 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    thisServerIP = s.getsockname()[0]
    s.close()
    
    return thisServerIP

# Global Variables 

clientList = [] # Stores the clients in the game (2 maximum)

# This function is used to see if client exists already in the list
def clientInList(clientIPAddrIn):
    foundClient = False # By default client is not found
    
    # Search through client list collection
    for clientEntry in clientList:
        if clientEntry[0] == clientIPAddrIn:
            foundClient = True
            break
    
    # Return the result
    return foundClient

# A function that is used to remove a client from the client list 
def removeClientFromList(ClientIPIn):
    clientRemoved = False
    icounter=0
    
    for client in clientList:
        if client[0] == ClientIPIn:
            break
        icounter = icounter + 1
            
    # Delete from list
    del clientList[icounter]

# Returns the length of the list of clients
def clientLimitedReached():
    limitReached = False # Return False by default
    
    # Check size of clientList
    if len(clientList) > 2:
        limitReached = True
    
    # Return the result
    return len(clientList)

# Determine the connection request from client
def getConnectionRequest(connectionRequestIn):
    connectionRequest = -1 # Connection request is invalid by default
    
    if connectionRequestIn == 'CONNECTTOSERVER1979':
        connectionRequest = 1 # Connection Request from Client
        
    if connectionRequestIn == 'TERMINATESERVER1979':
        connectionRequest = 2 # Termination Server Request from Client
        
    # Return result of connection request
    return connectionRequest

clientAddrPort = -1

# Server process
def setupServerListening():

    global clientAddrPort
    
    # Local variables
    serverTerminationMsg = "TERMINATESERVER1979"
    localIP     = "127.0.0.1"
    localPort   = 20001
    bufferSize  = 1024 

    msgFromServer       = "Hello UDP Client"
    bytesToSend         = str.encode(msgFromServer) 

    # Create a datagram socket

    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) 

    # Bind to address and ip

    UDPServerSocket.bind((localIP, localPort)) 

    print("UDP server up and listening") 

    # Listen for incoming datagrams

    while(True):

        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)

        message = bytesAddressPair[0]

        address = bytesAddressPair[1]
        clientAddrPort = bytesAddressPair[1]

        clientMsg = "Message from Client:{}".format(message)
        clientIP  = "Client IP Address:{}".format(address)                                                                                                                                                              
    
        print(clientMsg)
        print(clientIP)        
        
        # Converted Message - move higher up before reply sent to client 
        convertedMsg = str(message, "utf-8")
        
        msgSplit = convertedMsg.split(",")
        
        # Only process if valid connection request
        if getConnectionRequest(msgSplit[0]) > -1:
            if getConnectionRequest(msgSplit[0]) == 1:
                # Connection to server requested by client
                # Check to see if client is not in list
                if clientInList(msgSplit[1]) == False and clientLimitedReached() == False:
                    # Add client to list
                    clientIPMsg = msgSplit[1]
                    clientPortNo = msgSplit[2]
                    clientList.append([clientIPMsg, clientPortNo, getUKDateTime()])
                    # Form Message to client
                    msgFromServer = ("Connected to server " + str(getServerIPAddress()) + " @ " + getUKDateTime())
                    bytesToSend = str.encode(msgFromServer)
                    print("Adding Client to List")
                elif clientInList(msgSplit[1]) == True and clientLimitedReached() == False:
                    msgFromServer = ("Already connected to server...")
                    bytesToSend = str.encode(msgFromServer)
                    print("Client already connected...")
                elif clientLimitedReached() == True:
                    msgFromServer = ("Request Declined From Server")
                    bytesToSend = str.encode(msgFromServer)
                    print("Client Request to Server Declined")
                    
            if getConnectionRequest(msgSplit[0]) == 2:
                # Terminate from server by client request
                # Check to see if client is in the list
                if clientInList(msgSplit[1]) == True:
                    removeClientFromList(msgSplit[1])
                    msgFromServer = ("Connection Terminated @ " + getUKDateTime())
                    bytesToSend = str.encode(msgFromServer)
                    print("Client " + msgSplit[1] + " Disconnected From Server")
                else:
                    msgFromServer = ("Invalid Request")
                    bytesToSend = str.encode(msgFromServer)
                    print("Invalid Request sent by client")
                    
        
        # address[1] = 20002
        
        newClientIPAddrPort = (['127.0.0.1', 20002])
        print(newClientIPAddrPort)
        mytuple = tuple(newClientIPAddrPort)
        # Sending a reply to client
        UDPServerSocket.sendto(bytesToSend, mytuple)
        print(address)
        
threadedServerProcess = threading.Thread(target=setupServerListening)
threadedServerProcess.start()

# This method is used to self terminate the server
def selfTermination():
    # Form message to Client about server termination
    if len(clientList) > 0:
        print("Client(s) attached to server, still terminate server?")
        userchoice = input("Yes/No? ")
        
        if userchoice == "Yes":
            exit()
            
    else:
        exit()