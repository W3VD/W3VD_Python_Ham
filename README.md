# winKeyerServer.py

Interfaces with a K1EL WinKeyer. Creates a TCP server that other hosts on your network can send messages to be played on sidetone. Each message sent to the WinKeyer includes its own WPM and Farnsworth Character speed. Also echos paddle presses back to the host, which are sent to the network via multicast. This is not intended to send CW live on the radio. These tools are intended only to be used with a WinKeyer that is keying an AF code practice oscillator.

Python module pyserial is required, you can install with: 
```bash
pip install pyserial
```
You can set a default TTY/COM port in the script, but there is also an optional command line parameter you may use:
```bash
python ~/projects/W3VD_Python_Ham/winKeyerServer.py -p /dev/ttyUSB73
```
```bash
python c:\projects\W3VD_Python_Ham\winKeyerServer.py -p COM73
```

# winKeyerClient.py

Used to test the WinKeyer Server, or just play a desired message at a desired speed when you wish. Set the IP and port as appropriate in the script to match that of the TCP port of the WinKeyer Server. Run the script with no paramters. First 4 digits of the message must include the two digit word speed followed by the two digit character speed. For example, if you wanted to send "CQ CQ DE W3VD K" at 5 WPM word speed with a 15 WPM character speed you would enter:
```bash
0515CQ CQ DE W3VD K
```

# morseCodePractice.py
Stay tuned

# wsjt.py

Examines multicast traffic from WSJT-X. When TX mode is intiated, the DX callsign and grid square are read. If the grid square is present, it will set the DX station grid square in HamClock via the API. If the grid square is NOT present in WSJT-X, a QRZ lookup will be preformed, and the DX station grid will be set in HamClock. Also, the script will send the callsign 3 times to the WinKeyer Server to be played on CW sidetone.

I like F strings, and thus you will need Python 3.6 or later installed.

This script depends upon WSJTXClass.py which you can get at: https://github.com/rstagers/WSJT-X/blob/master/WSJTXClass.py

Python module requests is required, you can install with: 
```bash
pip install requests
```

WSJT-X must be setup for multicast, this allows any host on your subnet to read the traffic. Go to File, settings, reporting tab, change UDP server from 127.0.0.1 to 224.0.2.0. Any valid multicast address may be used instead of 224.0.2.0. You will have to configure any software such as Gridtracker, etc to listen to the same multi cast address instead of 127.0.0.1.

Edit the variables at the top of the file as appropriate.
