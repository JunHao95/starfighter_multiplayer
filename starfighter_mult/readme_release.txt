Release Notes for Multiplayer version of Star-Fighter
-----------------------------------------------------

Release notes as of: September 2021 by Andrew Smith

GUIDANCE NOTES
--------------

Remember to run both instances on same machine to use local host, set property in PlayerPrefs in game.py: multiplayerDemo = True

Tested on both Windows and Linux (Ubuntu) OS.


KNOWN ISSUES / FURTHER WORK TO BE DONE
--------------------------------------

Issues.....
- Position of power-ups / etc not consistent on client / server 
- Some random enemy behaviour not consistent on client / server
- Weapon upgrade not consistent on client / server 

Further possible work....
- Only basic authentication of client done when connecting
- No proper check of IP address entered when client mode selected (just takes it as is)
- Tested on LAN play using IP addresses on LAN network.  Not been developed for Internet play yet.  Further to be done on that.
	(A hack could be done to the code to enable Internet play with public IP addresses)

CODING
------

scenes.py
	- 3 classes implemented at the top of file:
		- MultiplayerMessage (A data structure to send a message)
		- MultiplayerDataTransferServer (A class for processing server operations)
		- MultiplayerDataTransferClient (A class for processing client operations)		
		  (All used in GameScene, update method further - mainly for data transfer between client and server)
		- MultiplayerOptionsScene
		
sprites.py
	- PlayerData class added to capture data from player to be updated on both server / client
	- Set/Get methods added to existing class Player to be used by PlayerData class
	
widgets.py
	- ServerClientConnectWidget
	- ClientScreenServerConnectWidget
	- MultiplayerOptionsSceneMenuWidget
	
defines.py
	- Various multiplayer constants added 
	
game.py
	- Various multiplayer properties added to PlayerPrefs
	
spawner.py
	- Modified constructor to accept a collection of players rather than just one player
	- Modified enemy player generation to become less random

	