import pygame, sys, random, math, pickle, threading, socket
from PIL import Image, ImageDraw
from data.scripts.spawner import Spawner
from data.scripts.sprites import Player
from data.scripts.sprites import PlayerData
from data.scripts.muda import (
    load_img, 
    load_sound, 
    sort,
    read_savedata,
    write_savedata,
    Scene,
    SceneManager,
    draw_background, 
    draw_text,
    shake,
    slice_list,
    clamp,
    image_at,
    scale_rect,
    draw_hpbar,
    draw_text2
)
from data.scripts.defines import *
from data.scripts.widgets import * 
from itertools import repeat
from datetime import datetime
import time

dataCollection = [] # Stores data to be sent accross 

# MULTIPLAYER DATA TRANSFER ====================================================

# Message to identify purpose to incoming communication
# Identifies purpose of the communication 
# Can be used for specific or general information
class MultiplayerMessage:
    def __init__(self, messageIn, ipDataIn, portDataIn):
        self.message = messageIn # Purpose of communication
        self.ipData = ipDataIn # IP address
        self.portData = portDataIn # Port Number

# Class for SERVER side operations 
class MultiplayerDataTransferServer:    
    
    def __init__(self, P_Prefs):
        # Player preferences
        self.P_Prefs = P_Prefs
        self.clientList = [] # Stores the clients in the game (2 maximum)
        
        if self.P_Prefs.multiplayerDemo == False:        
            self.serverIPAddress = self.getServerIPAddress()
            self.serverAddressPort = ([self.serverIPAddress, 20001])
        if self.P_Prefs.multiplayerDemo == True:
            self.serverIPAddress = '127.0.0.1'
            self.serverAddressPort = ([self.serverIPAddress, 20001])
        self.clientAddressPort = self.P_Prefs.clientAddressPort
        
        self.receiveCollection = [] # Collection used to receive from client
        self.sendCollection = [] # Collection used to send to client
        self.bufferSize = 8024
        self.HEADERSIZE = 10
		
    # Get's the current date and time and returns in UK format
    # Used on both client and server side (date and time logging)
    def getUKDateTime(self):
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
    def getServerIPAddress(self):
        # Get the server IP address 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        thisServerIP = s.getsockname()[0]
        s.close()
    
        return thisServerIP
        
        
    # This function is used to see if client exists already in the list
    def clientInList(self, clientIPAddrIn):
        foundClient = False # By default client is not found
    
        # Search through client list collection
        for clientEntry in self.clientList:
            if clientEntry[0] == clientIPAddrIn:
                foundClient = True
                break
    
        # Return the result
        return foundClient

    # Returns the length of the list of clients
    def clientLimitedReached(self):
        limitReached = False # Return False by default
    
        # Check size of clientList
        if len(self.clientList) > 1:
            limitReached = True
    
        # Return the result
        return len(self.clientList)
        
    # Determine the connection request from client
    def getConnectionRequest(self, connectionRequestIn):
        connectionRequest = -1 # Connection request is invalid by default
    
        if connectionRequestIn == 'CONNECTTOSERVER1979':
            connectionRequest = 1 # Connection Request from Client
            
        if connectionRequestIn == 'SELFSERVERTEMINATE':
            connectionRequest = 3 # Self-termination of server
        
        # Return result of connection request
        return connectionRequest

    # Method to send data to the client
    def sendDataToClient(self, objectDataIn):
        
        # Create a UDP socket at client side
        UDPServerClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        # Convert Object Data into byte data
        bytesToSend = pickle.dumps(objectDataIn)
        bytesToSend = bytes(f'{len(bytesToSend):<{self.HEADERSIZE}}', "utf-8") + bytesToSend

        # Over-ride if in multiplayer demo mode (Uses local host in demo mode)
        if self.P_Prefs.multiplayerDemo == True:
            self.P_Prefs.clientAddressPort = (['127.0.0.1', 20002])
        
        # Send to server using created UDP socket
        UDPServerClientSocket.sendto(bytesToSend, tuple(self.P_Prefs.clientAddressPort))    
    
    # Server process
    def setupServerListening(self):
    
        # Local variables
        localIP     = self.getServerIPAddress()

        # Create a socket
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) 

        # Over-ride IP address if in multiplayer demo mode
        if self.P_Prefs.multiplayerDemo == True:
            localIP = '127.0.0.1'

        UDPServerSocket.bind((localIP, self.P_Prefs.serverPort)) 

        # Listen for incoming communications
        while(True):

            # Get the data that is being transmitted from the client
            bytesAddressPair = UDPServerSocket.recvfrom(self.bufferSize)

            # Extract the data part of the communication stream            
            fulldataFromClient = bytesAddressPair[0]

            # Decode the data that has been recieved
            self.receiveCollection = pickle.loads(fulldataFromClient[self.HEADERSIZE:])
            
            # Get the message block part of the collection
            messageBlock = self.receiveCollection[0]
        
            # Only process if valid connection request
            if self.getConnectionRequest(messageBlock.message) > -1:
                if self.getConnectionRequest(messageBlock.message) == 1:
                    # Connection to server requested by client
                    # Check to see if client is not in list
                    if self.clientInList(messageBlock.ipData) == False and self.clientLimitedReached() == False:
                        # Add client to list
                        self.clientList.append([messageBlock.ipData, messageBlock.portData, self.getUKDateTime()])
                        
                        # Save client IP address and port number used for communication with client
                        if self.P_Prefs.multiplayerDemo == False:
                            self.clientAddressPort = ([messageBlock.ipData, 20002])
                            self.P_Prefs.clientAddressPort = self.clientAddressPort
                        elif self.P_Prefs.multiplayerDemo == True:
                            self.clientAddressPort = (['127.0.0.1', 20002])
                            self.P_Prefs.clientAddressPort = self.clientAddressPort
                        
                        # Set the message to send back
                        if self.P_Prefs.multiplayerDemo == False:
                            serverMsgToClient = MultiplayerMessage("SUCCESS", str(self.getServerIPAddress()), 20001)
                        elif self.P_Prefs.multiplayerDemo == True:
                            serverMsgToClient = MultiplayerMessage("SUCCESS", '127.0.0.1', 20001)
                        
                        # Clear sending list
                        self.sendCollection.clear()
                        
                        # Add the objects to send
                        self.sendCollection.append(serverMsgToClient)
                        
                        # Pickle the object and byte encode ready to send
                        bytesToSend = pickle.dumps(self.sendCollection)
                        bytesToSend = bytes(f'{len(bytesToSend):<{self.HEADERSIZE}}', "utf-8") + bytesToSend
                        
                        # Put in client address and port details          
                        newClientIPAddrPort = ([self.clientAddressPort[0], 20002])
                        #print(newClientIPAddrPort)
                        mytuple = tuple(newClientIPAddrPort)
                        # Sending a reply to client
                        
                        UDPServerSocket.sendto(bytesToSend, mytuple)
                        #print(address)                   

                if self.getConnectionRequest(messageBlock.message) == 3:
                    # Empty client list
                    self.clientList.clear()
                    return False # Terminate Server process
            
    # This method is used to self terminate the server
    def selfTermination(self, RequestToServerIn, serverAddressPort):
        # Form message to Client about server termination
        # Create a UDP socket at client side
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        # Create the message to send to server
        terminationMessage = MultiplayerMessage(RequestToServerIn, '0.0.0.0', 0)
        
        # Clear send data
        self.sendCollection.clear()
        
        # Add message to collection
        self.sendCollection.append(terminationMessage)
        
        # Pickle and encode data
        bytesToSend = pickle.dumps(self.sendCollection)
        bytesToSend = bytes(f'{len(bytesToSend):<{self.HEADERSIZE}}', "utf-8") + bytesToSend

        # Send to server using created UDP socket
        UDPClientSocket.sendto(bytesToSend, tuple(serverAddressPort)) 
        
# Class for the CLIENT side operations        
class MultiplayerDataTransferClient:

    # Constructor    
    def __init__(self, P_Prefs):        
        self.P_Prefs = P_Prefs
        
        if self.P_Prefs.multiplayerDemo == False:        
            self.serverAddressPort   = self.P_Prefs.serverAddressPort
            self.clientIPAddress = self.getClientIPAddress()
            self.clientAddressPort = ([self.clientIPAddress, 20002])
            
        if self.P_Prefs.multiplayerDemo == True:
            self.serverAddressPort = (['127.0.0.1', 20001])
            self.clientIPAddress = '127.0.0.1'
            self.clientAddressPort = ([self.clientIPAddress, 20002])
            
        self.bufferSize = 8024
        self.HEADERSIZE = 10
        
        self.objectCollection = [] # Used to recieve data objects in clientEndPoint
        self.sendCollection = [] # Used when sending communication to terminate
        
        # A flag to identify if client player is connected to server player
        self.connectedToServer = False
        
        # Identifies if a data transfer is in progress
        self.dataTransferInProgress = False
        
        
    # Get's the current date and time and returns in UK format
    # Used on both client and server side (date and time logging)
    def getUKDateTime(self):
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
    def getClientIPAddress(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        thisClientIP = s.getsockname()[0]
        s.close()
    
        return thisClientIP
        
    # This function is used to formulate a connection request to the server
    def sendConnectionRequest(self):        
        
        # Stores the data to send to the server
        clientDataCollection = []   
        
        # Form Connection Request
        if self.P_Prefs.multiplayerDemo == False:
            connReqTest = MultiplayerMessage("CONNECTTOSERVER1979", str(self.getClientIPAddress()), 20002)
        elif self.P_Prefs.multiplayerDemo == True:
            connReqTest = MultiplayerMessage("CONNECTTOSERVER1979", '127.0.0.1', 20002)
        
        clientDataCollection.append(connReqTest)
        serverConnectionReq = pickle.dumps(clientDataCollection)
        serverConnectionReq = bytes(f'{len(serverConnectionReq):<{self.HEADERSIZE}}', "utf-8") + serverConnectionReq
            
        # Send Connection Request to Server
        self.sendRequestToServer(serverConnectionReq)


    # This function is used to setup a client communication point for the 
    # server to communicate with
    def clientEndPoint(self):
        clientProcess = True # Flag to end the communication loop

        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) 
        
        # Bind to address and ip
        UDPClientSocket.bind((self.clientIPAddress, self.P_Prefs.clientPort)) 

        # Start client end point listening process
        while(clientProcess):

            # Only process data if a data transfer is not in progress
            if self.dataTransferInProgress == False:
                fulldata = UDPClientSocket.recv(self.bufferSize)            
                self.objectCollection = pickle.loads(fulldata[self.HEADERSIZE:])            
                dataMessage = self.objectCollection[0]
            
                # Identify successful connection to server
                if dataMessage.message == "SUCCESS" and self.connectedToServer == False:
                    self.connectedToServer = True
            
                # Self Termination Message for the client
                if dataMessage.message == "TERMINATECLIENT":
                    self.connectedToServer = False
                    clientProcess = False

    # A function that will send a request to the server 
    def sendRequestToServer(self, RequestToServerIn):
        # Create a UDP socket at client side
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        # Send to server using created UDP socket
        UDPClientSocket.sendto(RequestToServerIn, tuple(self.serverAddressPort))
        
    # Method to send data (game data) to the server
    def sendDataToServer(self, objectDataIn):

        # Create a UDP socket at client side
        UDPClientServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        # Convert Object Data into byte data
        bytesToSend = pickle.dumps(objectDataIn)
        bytesToSend = bytes(f'{len(bytesToSend):<{self.HEADERSIZE}}', "utf-8") + bytesToSend

        # Over-ride if in multiplayer demo mode
        if self.P_Prefs.multiplayerDemo == True:
            self.serverAddressPort = (['127.0.0.1', 20001])
        
        # Send to server using created UDP socket
        UDPClientServerSocket.sendto(bytesToSend, tuple(self.serverAddressPort)) 

    # This method is used to self terminate the client
    def selfTermination(self, RequestToServerIn, clientAddressPortIn):

        # Form message to Client about server termination
        # Create a UDP socket at client side
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        # Create the message to send to server
        terminationMessage = MultiplayerMessage(RequestToServerIn, '0.0.0.0', 0)
        
        # Clear send data
        self.sendCollection.clear()
        
        # Add message to collection
        self.sendCollection.append(terminationMessage)
        
        # Pickle and encode data
        bytesToSend = pickle.dumps(self.sendCollection)
        bytesToSend = bytes(f'{len(bytesToSend):<{self.HEADERSIZE}}', "utf-8") + bytesToSend

        # Send to server using created UDP socket
        UDPClientSocket.sendto(bytesToSend, tuple(clientAddressPortIn)) 

# TITLE SCENE ==================================================================

class TitleScene(Scene):
    def __init__(self, P_Prefs):
        # Player preferences
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Images
        self.logo_img = load_img("logo_notilt.png", IMG_DIR, 4, convert_alpha=False)
        self.logo_rect = self.logo_img.get_rect()
        self.logo_hw = self.logo_rect.width / 2

        # Menu object
        self.title_menu = TitleMenuWidget(self.P_Prefs.title_selected)

        # Logo bob
        self.bob_timer = pygame.time.get_ticks()
        self.bob_m = 0

        self.exit = False # Dumb hack to set running = False on the main loop

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                
                if event.key == self.P_Prefs.key_up:
                    self.title_menu.select_up()
                    self.sfx_keypress.play() # Play key press sound

                elif event.key == self.P_Prefs.key_down:
                    self.title_menu.select_down()
                    self.sfx_keypress.play() # Play key press sound

                elif event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                    self.sfx_keypress.play() # Play key press sound
                    
                    if self.title_menu.get_selected() == 0:
                        self.P_Prefs.title_selected = 0
                        # If Multiplayer Client, the below screen is not shown
                        # Instead, gets difficulty level set by server and
                        # goes straight to GameScene screen
                        if self.P_Prefs.multiplayer == 2:
                            # Client will go directly to GameScene via ClientScreenServerConnect
                            self.manager.go_to(ClientScreenServerConnect(self.P_Prefs))
                        else:
                            self.manager.go_to(DifficultySelectionScene(self.P_Prefs))

                    elif self.title_menu.get_selected() == 1:
                        self.P_Prefs.title_selected = 1
                        self.manager.go_to(ScoresScene(self.P_Prefs))

                    elif self.title_menu.get_selected() == 2:
                        self.P_Prefs.title_selected = 2
                        self.manager.go_to(OptionsScene(self.P_Prefs))

                    elif self.title_menu.get_selected() == 3:
                        self.P_Prefs.title_selected = 3
                        self.manager.go_to(CreditsScene(self.P_Prefs))

                    elif self.title_menu.get_selected() == 4:
                        self.exit = True

    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt
        self.title_menu.update()

    def draw(self, window):
        now = pygame.time.get_ticks()
        if now - self.bob_timer > 500:
            self.bob_timer = now 
            self.bob_m = 1 - self.bob_m

        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)
        window.blit(self.logo_img, (WIN_RES["w"]/2 - self.logo_hw, -64 + (2*self.bob_m)))

        # Draw menu
        self.title_menu.draw(window)
        #draw_text(window, "(Test Build v.Whatever)", int(FONT_SIZE/2), GAME_FONT, window.get_rect().centerx, 30, "WHITE", "centered")
        draw_text(window, f"Game v{VERSION}", int(FONT_SIZE/2), GAME_FONT, window.get_rect().centerx, window.get_rect().bottom-40, "WHITE", "centered")
        draw_text(window, "Pygame v2.0.1", int(FONT_SIZE/2), GAME_FONT, window.get_rect().centerx, window.get_rect().bottom-32, "WHITE", "centered")
        draw_text(window, "(c) 2020 zyenapz", int(FONT_SIZE/2), GAME_FONT, window.get_rect().centerx, window.get_rect().bottom-24, "WHITE", "centered")
        draw_text(window, "Code licensed under GPL-3.0", int(FONT_SIZE/2), GAME_FONT, window.get_rect().centerx, window.get_rect().bottom-16, "WHITE", "centered")
        draw_text(window, "Art licensed under CC BY-NC 4.0", int(FONT_SIZE/2), GAME_FONT, window.get_rect().centerx, window.get_rect().bottom-8, "WHITE", "centered")

# SCORES SCENE =================================================================

class ScoresScene(Scene):
    def __init__(self, P_Prefs):
        # Player preferences
        self.P_Prefs = P_Prefs

        # Load scores list
        self.scores_list = list()
        try:
            with open(SCORES_FILE, 'rb') as f:
                self.scores_list = pickle.load(f)
        except:
            pass

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Scores table
        self.scores_table = ScoresTableWidget(self.scores_list)

        # Control panel
        self.control_widget = ScoresControlWidget()

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == self.P_Prefs.key_left:
                    self.sfx_keypress.play() # Play keypress sound
                    self.control_widget.move_left()
                elif event.key == self.P_Prefs.key_right:
                    self.sfx_keypress.play() # Play keypress sound
                    self.control_widget.move_right()
                elif event.key == self.P_Prefs.key_up:
                    self.sfx_keypress.play() # Play keypress sound
                    self.control_widget.move_up()
                elif event.key == self.P_Prefs.key_down:
                    self.sfx_keypress.play() # Play keypress sound
                    self.control_widget.move_down()

                elif event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:

                    if self.control_widget.get_active_panel() == "DIRECTION":

                        if self.control_widget.get_dp_selected_option() == "PREV":
                            if self.scores_table.cur_tbl > 0:
                                self.sfx_keypress.play() # Play keypress sound

                            self.scores_table.prev_table()

                        elif self.control_widget.get_dp_selected_option() == "NEXT":
                            if self.scores_table.cur_tbl < len(self.scores_table.scores) - 1:
                                self.sfx_keypress.play() # Play keypress sound

                            self.scores_table.next_table()

                    elif self.control_widget.get_active_panel() == "BACK":
                        self.sfx_keypress.play() # Play keypress sound
                        self.manager.go_to(TitleScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_back:
                    self.sfx_keypress.play() # Play keypress sound
                    self.manager.go_to(TitleScene(self.P_Prefs))
    
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "HALL OF FAME", FONT_SIZE*2, GAME_FONT, window.get_rect().centerx, 64, "WHITE", "centered")
        self.scores_table.draw(window)
        self.control_widget.draw(window)

# OPTIONS SCENE ================================================================

class OptionsScene(Scene):
    def __init__(self, P_Prefs):
        self.P_Prefs = P_Prefs
        
        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Menu widget
        self.menu_widget = OptionsSceneMenuWidget(self.P_Prefs.options_scene_selected)

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:

                # Key press events
                if event.key == self.P_Prefs.key_back:
                    self.sfx_keypress.play() # Play key press sound
                    self.P_Prefs.options_scene_selected = 0
                    self.manager.go_to(TitleScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_up:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_up()

                elif event.key == self.P_Prefs.key_down:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_down()
                
                elif event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                    self.sfx_keypress.play() # Play key press sound

                    if self.menu_widget.get_selected_str() == "VIDEO":
                        self.P_Prefs.options_scene_selected = 0
                        self.manager.go_to(VideoOptionsScene(self.P_Prefs))

                    elif self.menu_widget.get_selected_str() == "SOUND":
                        self.P_Prefs.options_scene_selected = 1
                        self.manager.go_to(SoundOptionsScene(self.P_Prefs))

                    elif self.menu_widget.get_selected_str() == "GAME":
                        self.P_Prefs.options_scene_selected = 2
                        self.manager.go_to(GameOptionsScene(self.P_Prefs))

                    elif self.menu_widget.get_selected_str() == "CONTROLS":
                        self.P_Prefs.options_scene_selected = 3
                        self.manager.go_to(ControlsOptionsScene(self.P_Prefs))
                        
                    # Control for multiplayer option
                    elif self.menu_widget.get_selected_str() == "MULTIPLAYER":
                        self.P_Prefs.options_scene_selected = 4
                        self.manager.go_to(MultiplayerOptionsScene(self.P_Prefs))

                    elif self.menu_widget.get_selected_str() == "BACK":
                        self.P_Prefs.options_scene_selected = 0
                        self.manager.go_to(TitleScene(self.P_Prefs))
    
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.menu_widget.update()

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "OPTIONS", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        self.menu_widget.draw(window)

class VideoOptionsScene(Scene):
    def __init__(self, P_Prefs):
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Menu widget
        self.menu_widget = VideoOptionsSceneMenuWidget(self.P_Prefs)

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:

                # Key press events
                if event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                    self.sfx_keypress.play() # Play key press sound

                    if self.menu_widget.get_selected() == self.menu_widget.get_max_index():
                        self.manager.go_to(OptionsScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_back:
                    self.sfx_keypress.play() # Play key press sound
                    self.manager.go_to(OptionsScene(self.P_Prefs))
                
                elif event.key == self.P_Prefs.key_up:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_up()

                elif event.key == self.P_Prefs.key_down:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_down()

                elif event.key == self.P_Prefs.key_left:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_left()

                elif event.key == self.P_Prefs.key_right:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_right()

    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.menu_widget.update()

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "VIDEO OPTIONS", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        self.menu_widget.draw(window)

class SoundOptionsScene(Scene):
    def __init__(self, P_Prefs):
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Menu widget
        self.menu_widget = SoundOptionsSceneMenuWidget(self.P_Prefs)

        # Key press delay
        self.press_timer = pygame.time.get_ticks()
        self.press_delay = 75

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)

    def handle_events(self, events):
        # KEYDOWN EVENTS
        for event in events:
            if event.type == pygame.KEYDOWN:

                if event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                    self.sfx_keypress.play() # Play key press sound

                    if self.menu_widget.get_selected() == self.menu_widget.get_max_index():
                        self.manager.go_to(OptionsScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_back:
                    self.sfx_keypress.play() # Play key press sound
                    self.manager.go_to(OptionsScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_up:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_up()

                elif event.key == self.P_Prefs.key_down:
                    self.sfx_keypress.play() # Play key press sound
                    self.menu_widget.select_down()

        # Volume knob key presses
        now = pygame.time.get_ticks()
        if now - self.press_timer > self.press_delay:
            self.press_timer = now

            pressed = pygame.key.get_pressed()
            if pressed[self.P_Prefs.key_left]:
                self.menu_widget.select_left()

            elif pressed[self.P_Prefs.key_right]:
                self.menu_widget.select_right()

    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        # Update preferences
        self.P_Prefs.sfx_vol = self.menu_widget.rs_sfx.get_value() / 100
        self.P_Prefs.music_vol = self.menu_widget.rs_ost.get_value() / 100

        # Update sound volumes
        self.sfx_keypress.set_volume(self.P_Prefs.sfx_vol)

        self.menu_widget.update()

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "SOUND OPTIONS", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        self.menu_widget.draw(window)

class GameOptionsScene(Scene):
    def __init__(self, P_Prefs):
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Menu widget
        self.menu_widget = GameOptionsSceneMenuWidget(self.P_Prefs)

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:

                if event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                    self.sfx_keypress.play() # Play sound
                    if self.menu_widget.get_selected() == self.menu_widget.get_max_index():
                        self.manager.go_to(OptionsScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_back:
                    self.sfx_keypress.play() # Play sound
                    self.manager.go_to(OptionsScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_up:
                    self.sfx_keypress.play() # Play sound
                    self.menu_widget.select_up()

                elif event.key == self.P_Prefs.key_down:
                    self.sfx_keypress.play() # Play sound
                    self.menu_widget.select_down()

                elif event.key == self.P_Prefs.key_left:
                    self.sfx_keypress.play() # Play sound
                    self.menu_widget.select_left()

                elif event.key == self.P_Prefs.key_right:
                    self.sfx_keypress.play() # Play sound
                    self.menu_widget.select_right()

    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.menu_widget.update()

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "GAME OPTIONS", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        self.menu_widget.draw(window)

class ControlsOptionsScene(Scene):
    def __init__(self, P_Prefs):
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Menu widget
        self.menu_widget = ControlsOptionsSceneMenuWidget(self.P_Prefs)

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if not self.menu_widget.is_changingkey:
                    if event.key == self.P_Prefs.key_up:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_up()

                    elif event.key == self.P_Prefs.key_down:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_down()

                    elif event.key == self.P_Prefs.key_left:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_left()

                    elif event.key == self.P_Prefs.key_right:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_right()

                    elif event.key == pygame.K_RETURN and self.menu_widget.get_selected() != self.menu_widget.get_max_index():
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.highlight()

                    elif event.key == self.P_Prefs.key_back:
                        self.sfx_keypress.play() # Play sound
                        self.manager.go_to(OptionsScene(self.P_Prefs))
                        self.menu_widget.save_prefs()

                    elif event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                        if self.menu_widget.get_selected() == self.menu_widget.get_max_index():
                            self.sfx_keypress.play() # Play sound
                            self.manager.go_to(OptionsScene(self.P_Prefs))
                            self.menu_widget.save_prefs()
                else:
                    if event.key == pygame.K_RETURN:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.unhighlight()
                    else:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.change_key(event.key)
                        
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.menu_widget.update()

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "CONTROLS", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        self.menu_widget.draw(window)
        
        

class MultiplayerOptionsScene(Scene):
    def __init__(self, P_Prefs):
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0
        self.user_text = ' '

        # Menu widget
        self.menu_widget = MultiplayerOptionsSceneMenuWidget(self.P_Prefs)

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.user_text += event.unicode
                
                # Display server IP as user types IP address in
                self.menu_widget.displayUserIP(self.user_text)
            
                if not self.menu_widget.is_changingkey:
                    if event.key == self.P_Prefs.key_up:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_up()

                    elif event.key == self.P_Prefs.key_down:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_down()

                    elif event.key == self.P_Prefs.key_left:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_left()

                    elif event.key == self.P_Prefs.key_right:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.select_right()

                    elif event.key == pygame.K_RETURN and self.menu_widget.get_selected() != self.menu_widget.get_max_index():
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.highlight()

                    elif event.key == self.P_Prefs.key_back:
                        self.sfx_keypress.play() # Play sound

                    elif event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                        if self.menu_widget.get_selected() == self.menu_widget.get_max_index():
                            self.sfx_keypress.play() # Play sound
                            if self.P_Prefs.multiplayerDemo == False:
                                servIPAddress = self.user_text
                                servIPAddress = servIPAddress.strip()
                                self.P_Prefs.serverIPAddress = servIPAddress
                                self.P_Prefs.serverAddressPort = ([servIPAddress,20001])
                            
                            if self.P_Prefs.multiplayerDemo == True:
                                self.P_Prefs.serverIPAddress = '127.0.0.1'
                                self.P_Prefs.serverAddressPort = ([self.P_Prefs.serverIPAddress,20001])
                            
                            self.manager.go_to(OptionsScene(self.P_Prefs))
                            self.menu_widget.save_prefs()
                else:
                    if event.key == pygame.K_RETURN:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.unhighlight()
                    else:
                        self.sfx_keypress.play() # Play sound
                        self.menu_widget.change_key(event.key)
                        
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.menu_widget.update()

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "MULTIPLAYER", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        self.menu_widget.draw(window)

# CREDITS SCENE ================================================================

class CreditsScene(Scene):
    def __init__(self, P_Prefs):
        # Player preferences
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Button
        self.back_button = pygame.Surface((128,32))
        self.back_button.fill("WHITE")

        # Devs' pictures
        DEVS_SHEET = load_img("devs_sheet.png", IMG_DIR, SCALE)
        self.zye_icon = image_at(DEVS_SHEET, scale_rect(SCALE, [0,0,16,16]), True)
        self.rio_icon = image_at(DEVS_SHEET, scale_rect(SCALE, [16,0,16,16]), True)

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.sfx_keypress.play()
                if event.key == self.P_Prefs.key_back or event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                    self.manager.go_to(TitleScene(self.P_Prefs))
    
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "CREDITS", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        window.blit(self.zye_icon, (WIN_RES["w"]/2 - self.zye_icon.get_width()/2, WIN_RES["h"]*0.20))
        draw_text2(window, "zyenapz", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.270), "YELLOW", align="center")
        draw_text2(window, "code,art,sfx", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.300), "WHITE", align="center")

        window.blit(self.rio_icon, (WIN_RES["w"]/2 - self.rio_icon.get_width()/2, WIN_RES["h"]*0.350))
        draw_text2(window, "YoItsRion", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.430), "YELLOW", align="center")
        draw_text2(window, "music", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.460), "WHITE", align="center")
        
        draw_text2(window, "Andrew Smith", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.430+30), "YELLOW", align="center")
        draw_text2(window, "network programming", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.460+40), "WHITE", align="center")

        draw_text2(window, "Special thanks", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.560+45), "WHITE", align="center")
        draw_text2(window, "@ooshkei,", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.600+50), "WHITE", align="center")
        draw_text2(window, "my friends,", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.640+55), "WHITE", align="center")
        draw_text2(window, "the pygame community,", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.680+60), "WHITE", align="center")
        draw_text2(window, "and you!", GAME_FONT, FONT_SIZE, (WIN_RES["w"]/2, WIN_RES["h"]*0.720+65), "WHITE", align="center")

        draw_text2(
            self.back_button, 
            "BACK", 
            GAME_FONT, 
            FONT_SIZE, 
            (self.back_button.get_width()/2 - FONT_SIZE, self.back_button.get_height()/2 - FONT_SIZE/2), 
            "BLACK", 
            align="center"
        )
        window.blit(self.back_button, (window.get_width()/2 - self.back_button.get_width()/2,window.get_rect().height*0.8+20))

# DIFFICULTY SELECTION SCENE ================================================================

class DifficultySelectionScene(Scene):
    def __init__(self, P_Prefs):
        # Player preferences
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Difficulty Menu widget
        DEFAULT_SELECTED = 1
        self.w_diffmenu = DifficultyMenuWidget(DEFAULT_SELECTED)
        self.selected_diff = DEFAULT_SELECTED

        # Difficulty icons
        DIFFICULTY_SPRITESHEET = load_img("difficulty_sheet.png", IMG_DIR, SCALE*2)
        self.DIFFICULTY_ICONS = {
            0: image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE*2, [0,0,16,16]), True),
            1: image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE*2, [0,16,16,16]), True),
            2: image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE*2, [0,32,16,16]), True)
        }

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == self.P_Prefs.key_up:
                    self.sfx_keypress.play() # Play sound
                    self.w_diffmenu.select_up()
                    self.selected_diff = self.w_diffmenu.get_selected()

                elif event.key == self.P_Prefs.key_down:
                    self.sfx_keypress.play() # Play sound
                    self.w_diffmenu.select_down()
                    self.selected_diff = self.w_diffmenu.get_selected()

                elif event.key == self.P_Prefs.key_fire or event.key == pygame.K_RETURN:
                    self.sfx_keypress.play() # Play sound

                    if self.w_diffmenu.get_selected_str() != "BACK":
                        self.P_Prefs.game_difficulty = self.selected_diff
                        # Check for multiplayer here...if multiplayer option selected
                        # If server, message on screen - waiting for Client to Connect....
                        if self.P_Prefs.multiplayer == 1 or self.P_Prefs.multiplayer == 2:
                            self.manager.go_to(ServerScreenClientConnect(self.P_Prefs))
                        else:
                            self.manager.go_to(GameScene(self.P_Prefs))
                        
                    elif self.w_diffmenu.get_selected_str() == "BACK":
                        self.manager.go_to(TitleScene(self.P_Prefs))

                elif event.key == self.P_Prefs.key_back:
                    self.sfx_keypress.play() # Play sound
                    self.manager.go_to(TitleScene(self.P_Prefs))
    
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.w_diffmenu.update()

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "SELECT DIFFICULTY", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        try:
            window.blit(
                self.DIFFICULTY_ICONS[self.selected_diff], 
                (window.get_width()/2 - self.DIFFICULTY_ICONS[self.selected_diff].get_width() / 2, window.get_height()*0.30)
            )
        except:
            pass
        self.w_diffmenu.draw(window)
        
# SERVER SCREEN - WAITING FOR CLIENT TO CONNECT ================================

class ServerScreenClientConnect(Scene):
    def __init__(self, P_Prefs):
        # Player preferences
        self.P_Prefs = P_Prefs

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # ServerScreeenClientConnect widget
        DEFAULT_SELECTED = 1
        self.w_diffmenu = ServerClientConnectWidget(DEFAULT_SELECTED, P_Prefs)
        self.selected_diff = DEFAULT_SELECTED
        self.clientConnMessageShown = False;
        
        # Start up the server listening process
        self.mpserver = MultiplayerDataTransferServer(P_Prefs)
        
        self.threadedServerProcess = threading.Thread(target=self.mpserver.setupServerListening)
        self.threadedServerProcess.start()  

    # Handle key down events
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Kill thread process and go back to title screen           
                    self.mpserver.selfTermination("SELFSERVERTEMINATE", self.mpserver.serverAddressPort)
                    self.threadedServerProcess.join()
                    self.manager.go_to(TitleScene(self.P_Prefs))
                    
                    
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.w_diffmenu.update()
        
        if self.clientConnMessageShown == True:
            time.sleep(2)
            self.mpserver.selfTermination("SELFSERVERTEMINATE", self.mpserver.serverAddressPort)
            self.threadedServerProcess.join()
            self.manager.go_to(GameScene(self.P_Prefs))
            
           

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "PLEASE WAIT...", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        if len(self.mpserver.clientList) > 0:
            draw_text(window, "PLAYER JOINED GAME", FONT_SIZE, GAME_FONT, WIN_RES["w"]/2, 300, "GREEN", "centered")
            self.clientConnMessageShown = True
        try:
            window.blit(
                self.DIFFICULTY_ICONS[self.selected_diff], 
                (window.get_width()/2 - self.DIFFICULTY_ICONS[self.selected_diff].get_width() / 2, window.get_height()*0.30)
            )
        except:
            pass
        self.w_diffmenu.draw(window)
        
# ClientScreenServerConnect Scene

class ClientScreenServerConnect:
    def __init__(self, P_Prefs):
        self.P_Prefs = P_Prefs
        
        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0
        
        # ServerScreeenClientConnect widget
        DEFAULT_SELECTED = 1
        self.w_diffmenu = ClientScreenServerConnectWidget(P_Prefs)
        self.selected_diff = DEFAULT_SELECTED
        self.clientConnMessageShown = False;
        
        # Create client object
        self.mpClient = MultiplayerDataTransferClient(P_Prefs)
        
        # Setup client based server for listening to feedback from the server
        self.threadedClientProcess = threading.Thread(target=self.mpClient.clientEndPoint)
        self.threadedClientProcess.start()  
        
        # Send a connection request to the server
        self.mpClient.sendConnectionRequest()        

    # Handle key down events
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.go_to(TitleScene(self.P_Prefs))
                    
                    
    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

        self.w_diffmenu.update()
        
        if self.mpClient.connectedToServer == True and self.clientConnMessageShown == True:
            time.sleep(2)
            self.mpClient.selfTermination("TERMINATECLIENT", self.mpClient.clientAddressPort)
            self.threadedClientProcess.join()
            self.manager.go_to(GameScene(self.P_Prefs))

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        draw_text(window, "PLEASE WAIT...", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")   
        if self.mpClient.connectedToServer == True:
            draw_text(window, "CONNECTED TO SERVER...JOINING GAME!", FONT_SIZE, GAME_FONT, WIN_RES["w"]/2, 300, "GREEN", "centered")
            self.clientConnMessageShown = True        
        try:
            window.blit(
                self.DIFFICULTY_ICONS[self.selected_diff], 
                (window.get_width()/2 - self.DIFFICULTY_ICONS[self.selected_diff].get_width() / 2, window.get_height()*0.30)
            )
        except:
            pass
        self.w_diffmenu.draw(window)

# GAME SCENE ===================================================================

class GameScene(Scene):
    def __init__(self, P_Prefs):
        # Player Preferences
        self.P_Prefs = P_Prefs

        # SCENE DEFINES 
        self.g_diff = DIFFICULTIES[self.P_Prefs.game_difficulty]
        self.score = 0
        self.score_multiplier = SCORE_MULTIPLIER[self.g_diff]
        self.win_offset = repeat((0,0)) 
        self.hp_pref = HP_OPTIONS[self.P_Prefs.hp_pref]
        self.gg_timer = pygame.time.get_ticks()
        self.gg_delay = 3000
        self.is_gg = False
        self.can_pause = self.P_Prefs.can_pause
        self.paused = False

        # PLAYER AND BULLET IMAGES - If you are reading this...uhh...good luck lol
        PLAYER_SPRITESHEET = load_img("player_sheet.png", IMG_DIR, SCALE)
        PLAYER_IMGS = {
            "SPAWNING": [
                image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,144,16,16]), True),
                image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,144,16,16]), True),
                image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,144,16,16]), True),
                image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,144,16,16]), True)
            ],
            "NORMAL": {
                "LV1": {
                    "FORWARD": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,0,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,0,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,0,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,0,16,16]), True)
                    ],
                    "LEFT": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,16,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,16,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,16,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,16,16,16]), True)
                    ],
                    "RIGHT": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,32,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,32,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,32,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,32,16,16]), True)
                    ]
                },
                "LV2": {
                    "FORWARD": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,48,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,48,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,48,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,48,16,16]), True)
                    ],
                    "LEFT": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,64,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,64,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,64,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,64,16,16]), True)
                    ],
                    "RIGHT": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,80,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,80,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,80,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,80,16,16]), True)
                    ]
                },
                "LV3": {
                    "FORWARD": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,96,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,96,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,96,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,96,16,16]), True)
                    ],
                    "LEFT": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,112,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,112,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,112,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,112,16,16]), True)
                    ],
                    "RIGHT": [
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,128,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,128,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,128,16,16]), True),
                        image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,128,16,16]), True)
                    ]
                }
            },
            "LEVELUP": {
                "1-2": [
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,160,16,16]), True),
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,160,16,16]), True),
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,160,16,16]), True),
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,160,16,16]), True)
                ],
                "2-3": [
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [0,176,16,16]), True),
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [16,176,16,16]), True),
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [32,176,16,16]), True),
                    image_at(PLAYER_SPRITESHEET, scale_rect(SCALE, [48,176,16,16]), True)
                ]
            }
        }
        BULLET_SPRITESHEET = load_img("bullet_sheet.png", IMG_DIR, SCALE)
        BULLET_IMG = image_at(BULLET_SPRITESHEET, scale_rect(SCALE, [16,0,8,8]), True)

        # BG AND PARALLAX IMAGES & DEFINES 
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # HP Bar Image
        self.hp_surf = pygame.Surface((128,16))
        self.hpbar_outline = load_img("hpbar_outline.png", IMG_DIR, SCALE)
        self.hpbar_color = load_img("hpbar_color.png", IMG_DIR, SCALE)

        # HP Pie Image
        PIE_SHEET = load_img("hppie_sheet.png", IMG_DIR, SCALE) # It's not a sheet for hippies
        self.pie_surf = pygame.Surface((32,32))
        self.pie_health = image_at(PIE_SHEET, scale_rect(SCALE, [0,0,16,16]), True)
        self.pie_outline = image_at(PIE_SHEET, scale_rect(SCALE, [16,0,16,16]), True)
        self.pie_rect = self.pie_surf.get_rect()
        self.pie_rect.x = WIN_RES["w"] * 0.77
        self.pie_rect.y = 4

        # Difficulty icons
        DIFFICULTY_SPRITESHEET = load_img("difficulty_sheet.png", IMG_DIR, SCALE)
        self.DIFFICULTY_ICONS = {
            "EASY": {
                "EARLY": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [0,0,16,16]), True),
                "MID": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [16,0,16,16]), True),
                "LATE": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [32,0,16,16]), True)
            },
            "MEDIUM": {
                "EARLY": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [0,16,16,16]), True),
                "MID": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [16,16,16,16]), True),
                "LATE": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [32,16,16,16]), True)
            },
            "HARD": {
                "EARLY": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [0,32,16,16]), True),
                "MID": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [16,32,16,16]), True),
                "LATE": image_at(DIFFICULTY_SPRITESHEET, scale_rect(SCALE, [32,32,16,16]), True)
            }
        }
        self.difficulty_icon = pygame.Surface((32,32))

        # Clear the sprite groups
        all_sprites_g.empty()
        hostiles_g.empty()
        p_bullets_g.empty()
        powerups_g.empty()
        e_bullets_g.empty()
        sentries_g.empty()
        hellfighters_g.empty()

        self.playerCollection = []
        
        # Initialize the player
        self.player = Player(PLAYER_IMGS, BULLET_IMG, self.P_Prefs)
        
        self.playerCollection.append(self.player)
        
        self.sendObjectCollection = [] # Objects for sending
        self.recObjectCollection = [] # Object store for receiving
        
        # Add second player to screen if multiplayer version is selected
        if self.P_Prefs.multiplayer == SERVER_MODE or self.P_Prefs.multiplayer == CLIENT_MODE:
            self.playerTwo = Player(PLAYER_IMGS, BULLET_IMG, self.P_Prefs)
            self.playerTwo.isMultiplayer = True
            all_sprites_g.add(self.playerTwo)
            self.playerCollection.append(self.playerTwo)
        
        all_sprites_g.add(self.player)

        # Create a spawner
        self.spawner = Spawner(self.playerCollection, self.g_diff, self.P_Prefs.multiplayer)

        # Exit progress bar
        self.exit_bar = pygame.Surface((32,32))
        self.exit_timer = pygame.time.get_ticks()
        self.exit_delay = 2000
        self.is_exiting = False
        self.timer_resetted = False

        # Killfeed
        self.scorefeed = Scorefeed()

        # Sounds
        self.sfx_explosions = [
            load_sound("sfx_explosion1.wav", SFX_DIR, self.P_Prefs.sfx_vol),
            load_sound("sfx_explosion2.wav", SFX_DIR, self.P_Prefs.sfx_vol),
            load_sound("sfx_explosion3.wav", SFX_DIR, self.P_Prefs.sfx_vol)
        ]
        self.sfx_hits = [
            load_sound("sfx_hit1.wav", SFX_DIR, self.P_Prefs.sfx_vol),
            load_sound("sfx_hit2.wav", SFX_DIR, self.P_Prefs.sfx_vol),
            load_sound("sfx_hit3.wav", SFX_DIR, self.P_Prefs.sfx_vol)
        ]
        self.sfx_powerup_gun = load_sound("sfx_powerup_gun.wav", SFX_DIR, self.P_Prefs.sfx_vol)
        self.sfx_powerup_hp = load_sound("sfx_powerup_hp.wav", SFX_DIR, self.P_Prefs.sfx_vol)
        self.sfx_powerup_coin = load_sound("sfx_powerup_coin.wav", SFX_DIR, self.P_Prefs.sfx_vol)
        self.sfx_powerup_sentry = load_sound("sfx_powerup_sentry.wav", SFX_DIR, self.P_Prefs.sfx_vol)
        
        # Create both server and client stub
        self.serverStub = MultiplayerDataTransferServer(self.P_Prefs)
        self.clientStub = MultiplayerDataTransferClient(self.P_Prefs)      
        
        # If acting as server, setup server listening thread
        if self.P_Prefs.multiplayer == SERVER_MODE:
            self.threadedServerProcess = threading.Thread(target=self.serverStub.setupServerListening)
            self.threadedServerProcess.start() 
        
        # If acting as client, setup client listening thread
        if self.P_Prefs.multiplayer == CLIENT_MODE:
            self.threadedClientProcess = threading.Thread(target=self.clientStub.clientEndPoint)
            self.threadedClientProcess.start()        

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_l and DEBUG_MODE:
                    self.player.gun_level += 1

                if self.can_pause and not self.is_gg:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = not self.paused # Dirty toggling hack
                    
                    if event.key == pygame.K_x and self.paused:
                        self.manager.go_to(TitleScene(self.P_Prefs))

        if not self.is_gg and not self.can_pause:
            pressed = pygame.key.get_pressed()
            if pressed[self.P_Prefs.key_back] or pressed[pygame.K_ESCAPE]:
                self.is_exiting = True
                if self.timer_resetted == False:
                    self.exit_timer = pygame.time.get_ticks()
                    self.timer_resetted = True
            else:
                self.is_exiting = False
                self.timer_resetted = False

        self.spawner.handle_events(events)
    
    def update(self, dt):
        if not self.paused:
            # Data Transfer
            if self.P_Prefs.multiplayer == SERVER_MODE: # Server-Mode
                
                # Data Transfer to Client (From Server)
                # Clear send object collection to reset
                self.sendObjectCollection.clear()
                sendGameDataObject = MultiplayerMessage('GAMEDATAFROMSERVER', '0.0.0.0', 0)
                self.sendObjectCollection.append(sendGameDataObject)

                # Add server data
                pData = PlayerData()

                # Add Server Player Data
                pData = self.player.getData()
                
                # Add Server Game Data
                pData.gameScore = self.score
                pData.gameEnd = self.is_gg                
                
                # Over-ride position details if the player is dead
                if self.player.isDead == True:
                    self.player.position = pygame.Vector2(-500,-500)
                    self.player.rect.x = -500
                    self.player.rect.y = -500
                    pData.isDead = True
                    pData.position = pygame.Vector2(-500,-500)
                    pData.rect.x = -500
                    pData.rect.y = -500
                
                # Add data to the collection
                self.sendObjectCollection.append(pData)       

                # Add client data
                pData2 = PlayerData()
                
                # Copy player two (client player) data
                pData2 = self.playerTwo.getData()
                
                # Over-ride position data if the player is dead
                if self.playerTwo.isDead == True:
                    self.playerTwo.position = pygame.Vector2(-500,-500)
                    self.playerTwo.rect.x = -500
                    self.playerTwo.rect.y = -500
                    pData2.position = Vec2(-500, -500)
                    pData2.rect.x = -500
                    pData2.rect.y = -500
                    pData2.isDead = True
                
                # Add Player Two Data to collection
                self.sendObjectCollection.append(pData2)
                
                # Send the data across to the client
                if len(self.sendObjectCollection) > 0:
                    self.serverStub.sendDataToClient(self.sendObjectCollection)
                    # Reset and Clear
                    self.sendObjectCollection.clear()                    
                if self.is_gg == True: # Game Over
                    self.threadedServerProcess.join()   
                    self.P_Prefs.score = self.score
                    self.manager.go_to(GameOverScene(self.P_Prefs))                
                #  Data Transfer from Client (To Server)
                if len(self.serverStub.receiveCollection) > 1 and self.is_gg == False:
                    # Get player data which has been received from the client
                    playerData = self.serverStub.receiveCollection[1]      

                    # Only update player Two position if alive
                    if self.playerTwo.isDead == False:
                        self.playerTwo.rect = playerData.rect                    
                        self.playerTwo.position = playerData.position
                        self.playerTwo.velocity = playerData.velocity
                        self.playerTwo.radius = playerData.radius        
                        self.playerTwo.speed = playerData.speed
                        self.playerTwo.gun_level = playerData.gun_level
                        self.playerTwo.prev_gunlv = playerData.prev_gunlv
                        self.playerTwo.hasFired = playerData.hasFired
                    
                    # Clear the received collection                
                    self.serverStub.receiveCollection.clear()
                
            if self.P_Prefs.multiplayer == CLIENT_MODE: # Client mode
                # Data Transfer from Server (To Client)
                if len(self.clientStub.objectCollection) > 1:                    
                    self.clientStub.dataTransferInProgress = True
                    # Player Two Data (Remote player)
                    playerData = self.clientStub.objectCollection[1]                    
                    
                    self.playerTwo.setData(playerData)
                    
                    # Get general game data
                    self.score = playerData.gameScore
                    self.is_gg = playerData.gameEnd
                    
                    # Player One Data (Client Player)
                    clientPlayerData = self.clientStub.objectCollection[2]
                    self.player.health = clientPlayerData.health
                    self.player.isDead = clientPlayerData.isDead
                    self.player.gun_level = clientPlayerData.gun_level
                    self.player.prev_gunlv = clientPlayerData.prev_gunlv
                    
                    if self.player.isDead == True:
                        self.player.position = pygame.Vector2(-500,-500)
                        self.player.rect.x = -500
                        self.player.rect.y = -500
                    
                    # Clear the received collection
                    self.clientStub.objectCollection.clear()     

                    # Identify data transfer has completed
                    self.clientStub.dataTransferInProgress = False
                
                if self.is_gg == True:
                    # Set-up and send termination message to server
                    self.sendObjectCollection.clear()
                    serverTerminationMsg = MultiplayerMessage('SELFSERVERTEMINATE', '0.0.0.0', 0)
                    self.sendObjectCollection.append(serverTerminationMsg)
                    self.clientStub.sendDataToServer(self.sendObjectCollection)
                    
                    # Terminate Client
                    self.clientStub.selfTermination('TERMINATECLIENT', self.clientStub.clientAddressPort)
                    
                    # Go to Game Over Scene
                    self.threadedClientProcess.join() 
                    self.P_Prefs.score = self.score
                    self.manager.go_to(GameOverScene(self.P_Prefs))
                if self.is_gg == False:
                
                    self.sendObjectCollection.clear()
                    # Identify Game Data From Client is to be sent
                    sendGameDataObject = MultiplayerMessage('GAMEDATAFROMCLIENT', '0.0.0.0', 0)
                    self.sendObjectCollection.append(sendGameDataObject)

                    # Add player data (self.player is remote player on server)
                    playerData = PlayerData()
                    playerData = self.player.getData()
                    
                    if self.player.isDead == True:
                        playerData.position = pygame.Vector2(-500,-500)
                        playerData.rect.x = -500
                        playerData.rect.y = -500
                        playerData.isDead = True
                        self.player.position = pygame.Vector2(-500,-500)
                        self.player.rect.x = -500
                        self.player.rect.y = -500
                    
                    self.sendObjectCollection.append(playerData)

                    # Send the data to the server
                    self.clientStub.sendDataToServer(self.sendObjectCollection)
                
                    # Reset and Clear the sent data collection
                    self.sendObjectCollection.clear()


            # Update parallax and background
            self.bg_y += BG_SPD * dt
            self.par_y += PAR_SPD * dt           

            # Player focus control for enemies
            if self.P_Prefs.multiplayer == 2:

                if self.playerTwo.isDead == True and self.player.isDead == False:
                    self.spawner.setPlayerFocus(self.player)
                    
                if self.playerTwo.isDead == False and self.player.isDead == True:
                    self.spawner.setPlayerFocus(self.playerTwo)
                    
                if self.playerTwo.isDead == False and self.player.isDead == False:
                    self.spawner.setPlayerFocus(self.playerTwo)
                    
            if self.P_Prefs.multiplayer == 1:

                if self.playerTwo.isDead == True and self.player.isDead == False:
                    self.spawner.setPlayerFocus(self.player)
                    
                if self.playerTwo.isDead == False and self.player.isDead == True:
                    self.spawner.setPlayerFocus(self.playerTwo)
                    
                if self.playerTwo.isDead == False and self.player.isDead == False:
                    self.spawner.setPlayerFocus(self.player)        

            # Exit progress
            if self.is_exiting:
                now = pygame.time.get_ticks()
                if now - self.exit_timer > self.exit_delay:
                    self.player.health -= PLAYER_HEALTH * 999
                    self.win_offset = shake(30,5)
                    self.is_exiting = False
            
            # Collisions
            if not self.is_gg:
                self._handle_collisions()

            # END GAME IF PLAYER HAS LESS THAN 0 HEALTH
            if self.P_Prefs.multiplayer == STANDALONE: # Stand-alone
                if self.player.health <= 0 and not self.is_gg:
                    # Play sound
                    random.choice(self.sfx_explosions).play()

                    # Spawn big explosion on player
                    bullet_x = self.player.rect.centerx
                    bullet_y = self.player.rect.centery
                    bullet_pos = Vec2(bullet_x, bullet_y)
                    self.spawner.spawn_explosion(bullet_pos, "BIG")

                    # Spawn explosion particles
                    self.spawner.spawn_exp_particles(
                        (self.player.rect.centerx, self.player.rect.centery),
                        (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                        100
                    )   

                    # Generate screen shake
                    self.win_offset = shake(30,5)

                    # Set to game over
                    self.player.kill()
                    self.is_gg = True
                    self.gg_timer = pygame.time.get_ticks()

                # Transition to game over scene if game is over
                if self.is_gg:
                    now = pygame.time.get_ticks()
                    if now - self.gg_timer > self.gg_delay:
                        self.P_Prefs.score = self.score
                        self.manager.go_to(GameOverScene(self.P_Prefs))

                self.spawner.update(self.score)
                self.scorefeed.update()
                all_sprites_g.update(dt)
            
            if self.P_Prefs.multiplayer == SERVER_MODE: # Server-mode                           
                if self.player.health <= 0 and self.player.isDead == False:
                        
                    random.choice(self.sfx_explosions).play()
                        
                    # Spawn big explosion on player
                    bullet_x = self.player.rect.centerx
                    bullet_y = self.player.rect.centery
                    bullet_pos = Vec2(bullet_x, bullet_y)
                    self.spawner.spawn_explosion(bullet_pos, "BIG")

                    # Spawn explosion particles
                    self.spawner.spawn_exp_particles(
                        (self.player.rect.centerx, self.player.rect.centery),
                        (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                        100
                        )  

                    # Generate screen shake
                    self.win_offset = shake(30,5)
                    
                    self.player.kill()
                    self.player.isDead = True
                    
                if self.playerTwo.health <= 0 and self.playerTwo.isDead == False:

                    random.choice(self.sfx_explosions).play()
                        
                    bullet_x = self.playerTwo.rect.centerx
                    bullet_y = self.playerTwo.rect.centery
                    bullet_pos = Vec2(bullet_x, bullet_y)
                    self.spawner.spawn_explosion(bullet_pos, "BIG")
                    
                    self.spawner.spawn_exp_particles(
                        (self.playerTwo.rect.centerx, self.playerTwo.rect.centery),
                        (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                        100
                        ) 

                    # Generate screen shake
                    self.win_offset = shake(30,5)
                    
                    self.playerTwo.kill()
                    all_sprites_g.update(dt)
                    self.playerTwo.isDead = True

                    # Set to game over
                if self.player.isDead and self.playerTwo.isDead:
                        self.player.kill()
                        self.playerTwo.kill()
                        self.is_gg = True
                        self.gg_timer = pygame.time.get_ticks()            

                # Transition to game over scene if game is over
                if self.is_gg == True:
                    now = pygame.time.get_ticks()
                    #if now - self.gg_timer > self.gg_delay:
                    self.P_Prefs.score = self.score

                self.spawner.update(self.score)
                self.scorefeed.update()
                all_sprites_g.update(dt)

            if self.P_Prefs.multiplayer == CLIENT_MODE: # Client-mode
                if self.player.health <= 0 and self.player.isDead == False:
                        
                    random.choice(self.sfx_explosions).play()
                        
                    # Spawn big explosion on player
                    bullet_x = self.player.rect.centerx
                    bullet_y = self.player.rect.centery
                    bullet_pos = Vec2(bullet_x, bullet_y)
                    self.spawner.spawn_explosion(bullet_pos, "BIG")

                    # Spawn explosion particles
                    self.spawner.spawn_exp_particles(
                        (self.player.rect.centerx, self.player.rect.centery),
                        (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                        100
                        )  

                    # Generate screen shake
                    self.win_offset = shake(30,5)
                    
                    self.player.kill()
                    all_sprites_g.update(dt)
                    self.player.isDead = True
                    
                if self.playerTwo.health <= 0 and self.playerTwo.isDead == False:

                    random.choice(self.sfx_explosions).play()
                        
                    bullet_x = self.playerTwo.rect.centerx
                    bullet_y = self.playerTwo.rect.centery
                    bullet_pos = Vec2(bullet_x, bullet_y)
                    self.spawner.spawn_explosion(bullet_pos, "BIG")
                    
                    self.spawner.spawn_exp_particles(
                        (self.playerTwo.rect.centerx, self.playerTwo.rect.centery),
                        (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                        100
                        ) 

                    # Generate screen shake
                    self.win_offset = shake(30,5)
                    
                    self.playerTwo.kill()
                    self.playerTwo.isDead = True

                # Set to game over
                if self.player.isDead and self.playerTwo.isDead:
                    self.player.kill()
                    self.playerTwo.kill()
                    self.is_gg = True
                    self.gg_timer = pygame.time.get_ticks()            

                # Transition to game over scene if game is over
                if self.is_gg == True:
                    now = pygame.time.get_ticks()
                    self.P_Prefs.score = self.score

                self.spawner.update(self.score)
                self.scorefeed.update()
                all_sprites_g.update(dt)

    def draw(self, window):
        if not self.paused:
            # Draw background
            draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
            draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

            # Draw sprites
            all_sprites_g.draw(window)
            
            # Draw score feed
            self.scorefeed.draw(window)

            # Draw exit progress
            self._draw_exitprogress(window)

            # Draw score
            cur_score = str(int(self.score)).zfill(6)
            draw_text2(window, f"{cur_score}", GAME_FONT, int(FONT_SIZE*1.4), (12, 10), HP_RED2, italic=True)
            draw_text2(window, f"{cur_score}", GAME_FONT, int(FONT_SIZE*1.4), (12, 8), "WHITE", italic=True)
            
            # Draw hp bar
            self._draw_hpbar(window)

            # Draw difficulty icon
            self.difficulty_icon = self.DIFFICULTY_ICONS[self.g_diff][self.spawner.current_stage]
            window.blit(self.difficulty_icon, (window.get_width() * 0.885,4))

            if self.is_gg:
                draw_text2(
                    window, 
                    "GAME OVER", 
                    GAME_FONT, 
                    int(FONT_SIZE*3), 
                    (window.get_width()/2, window.get_height()*0.4), 
                    "WHITE", 
                    italic=True, 
                    align="center"
                )

            # Draw debug text
            self._draw_debugtext(window)
        else:
            self._draw_pausetext(window)

    def _handle_collisions(self):
        # Call collision functions
        self._hostile_playerbullet_collide()
        self._player_enemybullet_collide()
        self._player_enemy_collide()
        self._player_powerup_collide()
        self._player_enemy_collide()
        self._sentry_enemy_collide()
        self._sentry_enemybullet_collide()

    def _hostile_playerbullet_collide(self):
        # HOSTILES - PLAYER BULLET COLLISION
        for bullet in p_bullets_g:
            hits = pygame.sprite.spritecollide(bullet, hostiles_g, False, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_hits).play()

                # Deduct enemy health
                hit.health -= self.player.BULLET_DAMAGE

                # Spawn small explosion
                bullet_x = bullet.rect.centerx
                bullet_y = bullet.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "SMALL")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    3
                )
                
                # Set boolean to True for flash effect
                hit.is_hurt = True

                # Kill bullet
                bullet.kill()

                # Logic if enemy is dead
                if hit.health <= 0:
                    # Play sound
                    random.choice(self.sfx_explosions).play()
                    
                    # Kill sprite
                    hit.kill()

                    if self.P_Prefs.multiplayer == 0 or self.P_Prefs.multiplayer == 1:
                        score_worth = hit.WORTH * self.score_multiplier
                        self.score += score_worth
                        self.scorefeed.add(score_worth)

                    # Spawn powerup
                    spawn_roll = random.randrange(1,100)
                    if spawn_roll <= POWERUP_ROLL_CHANCE[self.g_diff]:
                        self.spawner.spawn_powerup(hit.position)

                    # Spawn big explosion
                    bullet_x = hit.rect.centerx
                    bullet_y = hit.rect.centery
                    bullet_pos = Vec2(bullet_x, bullet_y)
                    self.spawner.spawn_explosion(bullet_pos, "BIG")

                    # Spawn explosion particles
                    self.spawner.spawn_exp_particles(
                        (hit.rect.centerx, hit.rect.centery),
                        (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                        30
                    )

                    # Generate screen shake
                    self.win_offset = shake(10,5)

    def _player_enemybullet_collide(self):
        # PLAYER - ENEMY BULLET COLLISION
        if self.P_Prefs.multiplayer == STANDALONE: # Stand-alone
            hits = pygame.sprite.spritecollide(self.player, e_bullets_g, True, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_hits).play()

                # Damage player
                self.player.health -= hit.DAMAGE

                # Spawn small explosion
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "SMALL")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    5
                )

                # Generate screen shake
                self.win_offset = shake(10,5)

                # Hurt player
                self.player.is_hurt = True
                
        if self.P_Prefs.multiplayer == SERVER_MODE: # Server-side
            hits = pygame.sprite.spritecollide(self.player, e_bullets_g, True, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_hits).play()

                # Damage player
                self.player.health -= hit.DAMAGE

                # Spawn small explosion
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "SMALL")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    5
                )

                # Generate screen shake
                self.win_offset = shake(10,5)

                # Hurt player
                self.player.is_hurt = True
                
            # Process the second player
            multiplayerHits = pygame.sprite.spritecollide(self.playerTwo, e_bullets_g, True, pygame.sprite.collide_circle)            
            for hit in multiplayerHits:
                # Play sound
                random.choice(self.sfx_hits).play()

                # Damage player    
                self.playerTwo.health -= hit.DAMAGE

                # Spawn small explosion
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "SMALL")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    5
                    )

                # Generate screen shake
                self.win_offset = shake(10,5)

                # Hurt player
                self.playerTwo.is_hurt = True
            
        if self.P_Prefs.multiplayer == CLIENT_MODE: # Client side
            multiplayerHits = pygame.sprite.spritecollide(self.player, e_bullets_g, True, pygame.sprite.collide_circle)
            
            for hit in multiplayerHits:
                # Play sound
                random.choice(self.sfx_hits).play()

                # Spawn small explosion
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "SMALL")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    5
                    )

                # Generate screen shake
                self.win_offset = shake(10,5)

                # Hurt player
                self.player.is_hurt = True
            
            
            multiplayerHits = pygame.sprite.spritecollide(self.playerTwo, e_bullets_g, True, pygame.sprite.collide_circle)
            
            for hit in multiplayerHits:
                # Play sound
                random.choice(self.sfx_hits).play()
                
                # Spawn small explosion
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "SMALL")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    5
                    )

                # Generate screen shake
                self.win_offset = shake(10,5)

                # Hurt player
                self.playerTwo.is_hurt = True


    def _player_enemy_collide(self):
        # PLAYER - ENEMY COLLISION
        if self.P_Prefs.multiplayer == STANDALONE: # Stand-alone mode
            hits = pygame.sprite.spritecollide(self.player, hostiles_g, True, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_explosions).play()

                self.player.health -= ENEMY_COLLISION_DAMAGE

                # Spawn big explosion on player
                bullet_x = self.player.rect.centerx
                bullet_y = self.player.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn big explosion on hit
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    EP_COLORS,
                    30
                )

                # Generate screen shake
                self.win_offset = shake(20,5)

                hit.kill()
        
        if self.P_Prefs.multiplayer == SERVER_MODE: # Server-mode

            hits = pygame.sprite.spritecollide(self.player, hostiles_g, True, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_explosions).play()

                self.player.health -= ENEMY_COLLISION_DAMAGE

                # Spawn big explosion on player
                bullet_x = self.player.rect.centerx
                bullet_y = self.player.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn big explosion on hit
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    EP_COLORS,
                    30
                )

                # Generate screen shake
                self.win_offset = shake(20,5)

                hit.kill()
                
            hits = pygame.sprite.spritecollide(self.playerTwo, hostiles_g, True, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_explosions).play()

                self.playerTwo.health -= ENEMY_COLLISION_DAMAGE

                # Spawn big explosion on player
                bullet_x = self.playerTwo.rect.centerx
                bullet_y = self.playerTwo.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn big explosion on hit
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    EP_COLORS,
                    30
                )

                # Generate screen shake
                self.win_offset = shake(20,5)

                hit.kill()
        
        if self.P_Prefs.multiplayer == CLIENT_MODE:            
            hitsMultiplayer = pygame.sprite.spritecollide(self.playerTwo, hostiles_g, True, pygame.sprite.collide_circle)
            for hit in hitsMultiplayer:
                # Play sound
                random.choice(self.sfx_explosions).play()

                # Spawn big explosion on player
                bullet_x = self.playerTwo.rect.centerx
                bullet_y = self.playerTwo.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn big explosion on hit
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    EP_COLORS,
                    30
                )

                # Generate screen shake
                self.win_offset = shake(20,5)

                hit.kill()
                
            hitsMultiplayer = pygame.sprite.spritecollide(self.player, hostiles_g, True, pygame.sprite.collide_circle)
            for hit in hitsMultiplayer:
                # Play sound
                random.choice(self.sfx_explosions).play()

                # Spawn big explosion on player
                bullet_x = self.player.rect.centerx
                bullet_y = self.player.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn big explosion on hit
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    EP_COLORS,
                    30
                )

                # Generate screen shake
                self.win_offset = shake(20,5)

                hit.kill()

    def _player_powerup_collide(self):
        # PLAYER - POWERUP COLLISION
        if self.P_Prefs.multiplayer == STANDALONE: # Stand-alone mode
            hits = pygame.sprite.spritecollide(self.player, powerups_g, True)
            for hit in hits:
                particles_color = ((255,255,255)) # Default case
                if hit.POW_TYPE == "GUN":
                    # Play sound 
                    self.sfx_powerup_gun.play()

                    # Gun level limit check / increase
                    if self.player.gun_level >= PLAYER_MAX_GUN_LEVEL:
                        self.player.gun_level = 3
                    else:
                        self.player.gun_level += 1

                    # Set particle colors
                    particles_color = GP_COLORS

                elif hit.POW_TYPE == "HEALTH":
                    # Play sound 
                    self.sfx_powerup_hp.play()

                    self.player.health += POWERUP_HEALTH_AMOUNT[self.g_diff]
                    if self.player.health >= PLAYER_MAX_HEALTH:
                        self.player.health = PLAYER_MAX_HEALTH
                    # Set particle colors
                    particles_color = HP_COLORS
                    
                elif hit.POW_TYPE == "SCORE":
                    # Play sound 
                    self.sfx_powerup_coin.play()

                    # Add score
                    p_score = POWERUP_SCORE_BASE_WORTH * self.score_multiplier
                    if self.P_Prefs.multiplayer == 0 and self.P_Prefs.multiplayer == 1:
                        self.score += p_score
                    self.scorefeed.add(p_score)

                    # Set particle colors
                    particles_color = SCR_COLORS

                elif hit.POW_TYPE == "SENTRY":
                    # Play sound 
                    self.sfx_powerup_sentry.play()

                    # Spawn sentry
                    self.spawner.spawn_sentry()

                    # Set particle colors
                    particles_color = SP_COLORS

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    particles_color,
                    30
                )

                # Produce a flashing effect
                # The player is not really hurt, the variable is just named that way because I was stupid
                # enough not to foresee other uses...now im too lazy to change it.
                self.player.is_hurt = True
            
        if self.P_Prefs.multiplayer == SERVER_MODE: # Server-mode
            
            # Process the remote player first (Player Two)
            hitsTwo = pygame.sprite.spritecollide(self.playerTwo, powerups_g, True)            
            
            for hit in hitsTwo:
                particles_color = ((255,255,255)) # Default case
                if hit.POW_TYPE == "GUN":
                    # Play sound 
                    self.sfx_powerup_gun.play()

                    # Gun level limit check / increase
                    if self.playerTwo.gun_level >= PLAYER_MAX_GUN_LEVEL:
                        self.playerTwo.gun_level = 3
                    else:
                        self.playerTwo.gun_level += 1

                    # Set particle colors
                    particles_color = GP_COLORS

                elif hit.POW_TYPE == "HEALTH":
                    # Play sound 
                    self.sfx_powerup_hp.play()

                    self.playerTwo.health += POWERUP_HEALTH_AMOUNT[self.g_diff]
                    if self.playerTwo.health >= PLAYER_MAX_HEALTH:
                        self.playerTwo.health = PLAYER_MAX_HEALTH
                    # Set particle colors
                    particles_color = HP_COLORS
                    
                elif hit.POW_TYPE == "SCORE":
                    # Play sound 
                    self.sfx_powerup_coin.play()

                    # Add score
                    p_score = POWERUP_SCORE_BASE_WORTH * self.score_multiplier
                    self.score += p_score
                    self.scorefeed.add(p_score)

                    # Set particle colors
                    particles_color = SCR_COLORS

                elif hit.POW_TYPE == "SENTRY":
                    # Play sound 
                    self.sfx_powerup_sentry.play()

                    # Spawn sentry
                    self.spawner.spawn_sentry()

                    # Set particle colors
                    particles_color = SP_COLORS

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    particles_color,
                    30
                )

                # Produce a flashing effect
                # The player is not really hurt, the variable is just named that way because I was stupid
                # enough not to foresee other uses...now im too lazy to change it.
                self.playerTwo.is_hurt = True
            
            # Process the server player (Player One)
            hits = pygame.sprite.spritecollide(self.player, powerups_g, True)            
            
            for hit in hits:
                particles_color = ((255,255,255)) # Default case
                if hit.POW_TYPE == "GUN":
                    # Play sound 
                    self.sfx_powerup_gun.play()

                    # Gun level limit check / increase
                    if self.player.gun_level >= PLAYER_MAX_GUN_LEVEL:
                        self.player.gun_level = 3
                    else:
                        self.player.gun_level += 1

                    # Set particle colors
                    particles_color = GP_COLORS

                elif hit.POW_TYPE == "HEALTH":
                    # Play sound 
                    self.sfx_powerup_hp.play()

                    self.player.health += POWERUP_HEALTH_AMOUNT[self.g_diff]
                    if self.player.health >= PLAYER_MAX_HEALTH:
                        self.player.health = PLAYER_MAX_HEALTH
                    # Set particle colors
                    particles_color = HP_COLORS
                    
                elif hit.POW_TYPE == "SCORE":
                    # Play sound 
                    self.sfx_powerup_coin.play()

                    # Add score
                    p_score = POWERUP_SCORE_BASE_WORTH * self.score_multiplier
                    self.score += p_score
                    self.scorefeed.add(p_score)

                    # Set particle colors
                    particles_color = SCR_COLORS

                elif hit.POW_TYPE == "SENTRY":
                    # Play sound 
                    self.sfx_powerup_sentry.play()

                    # Spawn sentry
                    self.spawner.spawn_sentry()

                    # Set particle colors
                    particles_color = SP_COLORS

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    particles_color,
                    30
                )

                # Produce a flashing effect
                # The player is not really hurt, the variable is just named that way because I was stupid
                # enough not to foresee other uses...now im too lazy to change it.
                self.player.is_hurt = True
        if self.P_Prefs.multiplayer == CLIENT_MODE: # Client-mode
            # Process the remote player first (Player Two)
            hitsTwo = pygame.sprite.spritecollide(self.playerTwo, powerups_g, True)            
            
            for hit in hitsTwo:
                particles_color = ((255,255,255)) # Default case
                if hit.POW_TYPE == "GUN":
                    # Play sound 
                    self.sfx_powerup_gun.play()

                    # Gun level limit check / increase
                    if self.playerTwo.gun_level >= PLAYER_MAX_GUN_LEVEL:
                        self.playerTwo.gun_level = 3
                    else:
                        self.playerTwo.gun_level += 1

                    # Set particle colors
                    particles_color = GP_COLORS

                elif hit.POW_TYPE == "HEALTH":
                    # Play sound 
                    self.sfx_powerup_hp.play()
                    particles_color = HP_COLORS
                    
                elif hit.POW_TYPE == "SCORE":
                    # Play sound 
                    self.sfx_powerup_coin.play()

                    # Set particle colors
                    particles_color = SCR_COLORS

                elif hit.POW_TYPE == "SENTRY":
                    # Play sound 
                    self.sfx_powerup_sentry.play()

                    # Spawn sentry
                    self.spawner.spawn_sentry()

                    # Set particle colors
                    particles_color = SP_COLORS

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    particles_color,
                    30
                )

                # Produce a flashing effect
                # The player is not really hurt, the variable is just named that way because I was stupid
                # enough not to foresee other uses...now im too lazy to change it.
                self.playerTwo.is_hurt = True
            
            # Process the server player (Player One)
            hits = pygame.sprite.spritecollide(self.player, powerups_g, True)            
            
            for hit in hits:
                particles_color = ((255,255,255)) # Default case
                if hit.POW_TYPE == "GUN":
                    # Play sound 
                    self.sfx_powerup_gun.play()

                    # Gun level limit check / increase
                    if self.player.gun_level >= PLAYER_MAX_GUN_LEVEL:
                        self.player.gun_level = 3
                    else:
                        self.player.gun_level += 1

                    # Set particle colors
                    particles_color = GP_COLORS

                elif hit.POW_TYPE == "HEALTH":
                    # Play sound 
                    self.sfx_powerup_hp.play()

                    particles_color = HP_COLORS
                    
                elif hit.POW_TYPE == "SCORE":
                    # Play sound 
                    self.sfx_powerup_coin.play()

                    # Set particle colors
                    particles_color = SCR_COLORS

                elif hit.POW_TYPE == "SENTRY":
                    # Play sound 
                    self.sfx_powerup_sentry.play()

                    # Spawn sentry
                    self.spawner.spawn_sentry()

                    # Set particle colors
                    particles_color = SP_COLORS

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    particles_color,
                    30
                )

                # Produce a flashing effect
                # The player is not really hurt, the variable is just named that way because I was stupid
                # enough not to foresee other uses...now im too lazy to change it.
                self.player.is_hurt = True
                

    def _sentry_enemy_collide(self):
        # SENTRY - ENEMY COLLISION
        for sentry in sentries_g:
            hits = pygame.sprite.spritecollide(sentry, hostiles_g, False, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_explosions).play()

                sentry.kill()
                hit.kill()

                # Spawn big explosion on sentry
                bullet_x = sentry.rect.centerx
                bullet_y = sentry.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn big explosion on hit
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "BIG")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    30
                )

    def _sentry_enemybullet_collide(self):
        # SENTRY - ENEMY BULLET COLLISION
        for sentry in sentries_g:
            hits = pygame.sprite.spritecollide(sentry, e_bullets_g, True, pygame.sprite.collide_circle)
            for hit in hits:
                # Play sound
                random.choice(self.sfx_hits).play()

                # Deduct sentry health
                sentry.health -= hit.DAMAGE

                # Set boolean to True for flash effect
                sentry.is_hurt = True

                # Spawn small explosion
                bullet_x = hit.rect.centerx
                bullet_y = hit.rect.centery
                bullet_pos = Vec2(bullet_x, bullet_y)
                self.spawner.spawn_explosion(bullet_pos, "SMALL")

                # Spawn explosion particles
                self.spawner.spawn_exp_particles(
                    (hit.rect.centerx, hit.rect.centery),
                    (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                    5
                )

                if sentry.health <= 0:
                    # Play sound
                    random.choice(self.sfx_explosions).play()
                    
                    # Spawn big explosion
                    bullet_x = sentry.rect.centerx
                    bullet_y = sentry.rect.centery
                    bullet_pos = Vec2(bullet_x, bullet_y)
                    self.spawner.spawn_explosion(bullet_pos, "BIG")

                    # Spawn explosion particles
                    self.spawner.spawn_exp_particles(
                        (sentry.rect.centerx, sentry.rect.centery),
                        (EP_YELLOW1, EP_YELLOW2, EP_YELLOW3),
                        30
                    )

                    sentry.kill()

    def _draw_exitprogress(self, window): 
        if self.is_exiting:
            now = pygame.time.get_ticks()
            bar_length = int((now - self.exit_timer) / 8)
            bar_color = "WHITE"
            if now - self.exit_timer > self.exit_delay / 2:
                bar_color = HP_RED1
            self.exit_bar = pygame.Surface((bar_length,16))
            self.exit_bar.fill(bar_color)
            draw_text2(
                self.exit_bar,
                "EXITING",
                GAME_FONT,
                FONT_SIZE,
                (self.exit_bar.get_width()/2, 0),
                "BLACK",
                align="center"
            )
            window.blit(
                self.exit_bar,
                (window.get_width()/2 - self.exit_bar.get_width()/2, window.get_height()/2)
            )

    def _draw_hpbar(self, window):
        if self.hp_pref == HP_OPTIONS[1]:
            # Draw square hp bar
            self.hp_surf.fill("BLACK")
            self.hp_surf.set_colorkey("BLACK")
            draw_hpbar(self.hp_surf, self.hpbar_color, (4,4,96,8), self.player.health, "WHITE")
            self.hp_surf.blit(self.hpbar_outline, (0,0))
            window.blit(self.hp_surf, 
                (
                    (window.get_width()/2) - 38,
                    10
                )
            )

        elif self.hp_pref == HP_OPTIONS[0]:
            # Draw circle hp bar
            semicirc_size = 32
            semicirc_end = 360 - (self.player.health * (360 / PLAYER_MAX_HEALTH)) + 270
            semicirc = Image.new("RGBA", (semicirc_size, semicirc_size))
            semicirc_d = ImageDraw.Draw(semicirc)
            semicirc_d.pieslice((0, 0, semicirc_size-1, semicirc_size-1), 271, semicirc_end + 1, fill="BLACK")
            semicirc_surf = pygame.image.fromstring(semicirc.tobytes(), semicirc.size, semicirc.mode)

            self.pie_surf.fill("BLACK")
            self.pie_surf.set_colorkey("BLACK")
            self.pie_surf.blit(self.pie_health, (0,0))
            self.pie_surf.blit(semicirc_surf, (0,0))
            self.pie_surf.blit(self.pie_outline, (0,0))
            window.blit(self.pie_surf, 
                (
                    window.get_width()/2,
                    4
                )
            )

    def _draw_debugtext(self, window):
        # Debug mode stats
        if DEBUG_MODE:
            draw_text(window, f"{int(self.score)}", FONT_SIZE, GAME_FONT, 48, 8, "WHITE", "centered")
            draw_text(window, f"HP: {int(self.player.health)}", FONT_SIZE, GAME_FONT, 48, 16 + FONT_SIZE, "WHITE", "centered")
            draw_text(window, f"STAGE: {self.spawner.current_stage}", FONT_SIZE, GAME_FONT, 48, 32 + FONT_SIZE, "WHITE")
            draw_text(window, f"DIFF: {self.g_diff}", FONT_SIZE, GAME_FONT, 48, 64 + FONT_SIZE, "WHITE", )

        window.blit(window, next(self.win_offset))

    def _draw_pausetext(self, window):
        draw_text2(
            window, 
            "PAUSED", 
            GAME_FONT, 
            int(FONT_SIZE*3), 
            (window.get_width()/2, window.get_height()*0.4), 
            "WHITE", 
            italic=True, 
            align="center"
        )
        draw_text2(
            window, 
            "ESC to Resume", 
            GAME_FONT, 
            int(FONT_SIZE*2), 
            (window.get_width()/2, window.get_height()*0.5), 
            "WHITE", 
            align="center"
        )
        draw_text2(
            window, 
            "X to Exit", 
            GAME_FONT, 
            int(FONT_SIZE*2), 
            (window.get_width()/2, window.get_height()*0.55), 
            "WHITE", 
            align="center"
        )

# GAME OVER SCENE ================================================================

class GameOverScene(Scene):
    def __init__(self, P_Prefs):
        # Player preferences 
        self.P_Prefs = P_Prefs

        # Scene variables
        self.score = self.P_Prefs.score
        self.name = str()
        self.bckspace_timer = pygame.time.get_ticks()
        self.bckspace_delay = 200
        self.MIN_CHAR = 2
        self.MAX_CHAR = 5
        self.score_comment = self._get_comment(self.score)
        self.difficulty = self.P_Prefs.game_difficulty

        # Background
        self.BG_IMG = load_img("background.png", IMG_DIR, SCALE)
        self.bg_rect = self.BG_IMG.get_rect()
        self.bg_y = 0
        self.PAR_IMG = load_img("background_parallax.png", IMG_DIR, SCALE)
        self.par_rect = self.BG_IMG.get_rect()
        self.par_y = 0

        # Enter button
        self.enter_button = pygame.Surface((128,32))
        self.enter_button.fill("WHITE")

        # Ranks
        RANKS_SHEET = load_img("ranks_sheet.png", IMG_DIR, SCALE*2)
        self.RANKS_IMGS = {
            "RECRUIT": image_at(RANKS_SHEET, scale_rect(SCALE*2, [0,0,16,16]), True),
            "ENSIGN": image_at(RANKS_SHEET, scale_rect(SCALE*2, [16,0,16,16]), True),
            "LIEUTENANT": image_at(RANKS_SHEET, scale_rect(SCALE*2, [32,0,16,16]), True),
            "COMMANDER": image_at(RANKS_SHEET, scale_rect(SCALE*2, [48,0,16,16]), True),
            "CAPTAIN": image_at(RANKS_SHEET, scale_rect(SCALE*2, [64,0,16,16]), True),
            "ADMIRAL": image_at(RANKS_SHEET, scale_rect(SCALE*2, [80,0,16,16]), True)
        }
        self.rank = self.score_comment.upper()

        # Sounds
        self.sfx_keypress = load_sound("sfx_keypress.wav", SFX_DIR, self.P_Prefs.sfx_vol)
    
    def handle_events(self, events):
        # Keydown events
        for event in events:
            if event.type == pygame.KEYDOWN:
                if str(event.unicode).isalpha() and len(self.name) < self.MAX_CHAR:
                    self.sfx_keypress.play()
                    self.name += event.unicode
                elif event.key == pygame.K_RETURN and len(self.name) >= self.MIN_CHAR:
                    self.sfx_keypress.play()
                    self._exit_scene()
        
        # Key presses event
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_BACKSPACE]:

            now = pygame.time.get_ticks()
            if now - self.bckspace_timer > self.bckspace_delay:
                if len(self.name) != 0:
                    self.sfx_keypress.play()

                self.bckspace_timer = now
                self.name = self.name[:-1]

    def update(self, dt):
        self.bg_y += BG_SPD * dt
        self.par_y += PAR_SPD * dt

    def draw(self, window):
        draw_background(window, self.BG_IMG, self.bg_rect, self.bg_y)
        draw_background(window, self.PAR_IMG, self.par_rect, self.par_y)

        # Draw game over and score
        draw_text(window, "GAME OVER!", FONT_SIZE*2, GAME_FONT, WIN_RES["w"]/2, 64, "WHITE", "centered")
        draw_text(window, f"{int(self.score)}", FONT_SIZE*4, GAME_FONT, WIN_RES["w"]/2, 104, HP_RED1, "centered")
        draw_text(window, f"{int(self.score)}", FONT_SIZE*4, GAME_FONT, WIN_RES["w"]/2, 100, "WHITE", "centered")

        # Draw rank and image
        #draw_text2(window, "Your Rank", GAME_FONT, int(FONT_SIZE*2), (WIN_RES["w"]/2, WIN_RES["h"]*0.35), "WHITE", align="center")
        try:
            window.blit(
                self.RANKS_IMGS[self.rank], 
                (window.get_width()/2 - self.RANKS_IMGS[self.rank].get_width()/2, window.get_height()*0.35)
            )
        except:
            pass
        draw_text2(window, f"Rank: {self.score_comment.capitalize()}", GAME_FONT, int(FONT_SIZE), (WIN_RES["w"]/2, WIN_RES["h"]*0.5), "WHITE", align="center")

        # if self.score_comment.upper() == "RECRUIT":
        #     draw_text2(window, f"You don't deserve symmetry", GAME_FONT, int(FONT_SIZE), (WIN_RES["w"]/2, WIN_RES["h"]*0.), "WHITE", align="center")

        # Draw  textbox
        if len(self.name) == 0:
            draw_text2(window, "ENTER NAME", GAME_FONT, int(FONT_SIZE*2), (WIN_RES["w"]/2, WIN_RES["h"]*0.645), "GRAY", align="center")
        else:
            draw_text2(window, f"> {self.name.upper()} <", GAME_FONT, int(FONT_SIZE*2), (WIN_RES["w"]/2, WIN_RES["h"]*0.645), "WHITE", align="center")
        
        # Draw enter button
        if len(self.name) >= self.MIN_CHAR:
            draw_text2(
                self.enter_button, 
                "ENTER", 
                GAME_FONT, 
                FONT_SIZE, 
                (self.enter_button.get_width()/2, (self.enter_button.get_height()/2) - FONT_SIZE / 2), 
                "BLACK", 
                align="center"
            )
            self.enter_button.set_colorkey("BLACK")
            window.blit(
                self.enter_button,
                (
                    window.get_width()/2 - self.enter_button.get_width()/2,
                    WIN_RES["h"]*0.75
                )
            )

    def _exit_scene(self):
        # Load scores list
        scores_list = list()
        try:
            with open(SCORES_FILE, 'rb') as f:
                scores_list = pickle.load(f)
        except:
            pass

        # Save score data to file
        score_dat = (self.name, int(self.score), self.difficulty)
        scores_list.append(score_dat)
        with open(SCORES_FILE, 'wb') as f:
            pickle.dump(scores_list, f)

        # Go to title scene
        self.manager.go_to(TitleScene(self.P_Prefs))

    def _get_comment(self, score):
        if score < 0:
            return "bugged"
        elif score == 0:
            return "recruit"
        elif score < 1000:
            return "ensign"
        elif score >= 1000 and score < 3000:
            return "lieutenant"
        elif score >= 3000 and score < 6000:
            return "commander"
        elif score >= 6000 and score < 9000:
            return "captain"
        elif score >= 9000:
            return "admiral"
