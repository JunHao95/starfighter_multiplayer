# Script: pickletest.py
# Author: Andrew Smith
# Date: August 2021
# Description: This script is used to test the unpacking of pickle data in bytes
#              When encoding is combined, string text with data objects

import pickle

# Class / Data Setup - Customer class

class Customer:
    def __init__(self, titleIn, surnameIn, firstnameIn, IdNoIn):
        self.title = titleIn
        self.surname = surnameIn
        self.firstname = firstnameIn
        self.idNo = IdNoIn
        
    def printDetails(self):
        print("Title: " + self.title)
        print("Surname: " + self.surname)
        print("Firstname: " + self.firstname)
        print("ID Number: " + str(self.idNo))

# Class / Data Setup - Order Class
class Order:
    def __init__(self, orderNoIn, orderProductDescIn, costPriceIn, quantityIn):
        self.orderNo = orderNoIn
        self.orderProductDescription = orderProductDescIn
        self.costPrice = costPriceIn
        self.quantity = quantityIn
        
    def printOrder(self):
        print("Order Number: " + str(self.orderNo))
        print("Product Description: " + self.orderProductDescription)
        print("Item Cost: " + str(self.costPrice))
        print("Quantity: " + str(self.quantity))
        
# The string to identify request
msg = 'DATATRANSFER,'

# Create some customer data objects
c1 = Customer("MR", "SMITH", "ANDREW", 1)
c2 = Customer("MR", "JENKINS", "DAVID", 2)
c3 = Customer("MR", "HOBBS", "JAKE", 3)
c4 = Customer("MISS", "BLOGGS", "JOANNE", 4)
c5 = Customer("MISS", "BRIDGEFORD", "VENESSA", 5)

# Create some order objects
o1 = Order(1, "XBOX ONE S EDITION", 399.99, 1)
o2 = Order(2, "PLAYSTATION 5", 599.99, 4)
o3 = Order(3, "PLAYSTATION 4", 149.99, 10)
o4 = Order(4, "LG PRINTER", 199.99, 4)
o5 = Order(5, "MICROWAVE", 79.99, 2)

# Put all class instances in a collection

objectCollection = [ ]

objectCollection.append(c1)
objectCollection.append(c2)
objectCollection.append(c3)
objectCollection.append(c4)
objectCollection.append(c5)
objectCollection.append(o1)
objectCollection.append(o2)
objectCollection.append(o3)
objectCollection.append(o4)
objectCollection.append(o5)

HEADERSIZE = 10

# Serialize object data
msgObjectData = pickle.dumps(objectCollection)

# Encode verification string
bytesIntro = str.encode(msg)

# Create the total data / message to be sent
totalmsg = (bytesIntro + msgObjectData)
totalmsg = bytes(f'{len(totalmsg):<{HEADERSIZE}}', "utf-8") + totalmsg

# Output the encoded message, totalmsg







        

