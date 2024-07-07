winKeyerServer.py - Stay tuned

winKeyerClient.py - Stay tuned

morseCodePractice.py - Stay tuned

wsjt.py

Examines multicast traffic from WSJT-X. When TX mode is intiated, the DX callsign and grid square are read. If the grid square is present, it will set the DX station grid square in HamClock via the API. If the grid square is NOT present in WSJT-X, a QRZ lookup will be preformed, and the DX station grid will be set in HamClock. Also, the script will send the callsign 3 times to the WinKeyer Server to be played on CW sidetone.

I like F strings, and thus you will need Python 3.6 or later installed.

This script depends upon WSJTXClass.py which you can get at: https://github.com/rstagers/WSJT-X/blob/master/WSJTXClass.py

Python module requests is required, you can install with: pip install requests

WSJT-X must be setup for multicast, this allows any host on your subnet to read the traffic. Go to File, settings, reporting tab, change UDP server from 127.0.0.1 to 224.0.2.0. Any valid multicast address may be used instead of 224.0.2.0. You will have to configure any software such as Gridtracker, etc to listen to the same multi cast address instead of 127.0.0.1.

Edit the variables at the top of the file as appropriate.
