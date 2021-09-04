# Script: getdtclient.py
# Author: Andrew Smith
# Description: A script the gets the date and time from a string

from datetime import datetime

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
    
    
    
    
