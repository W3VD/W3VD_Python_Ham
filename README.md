wsjt.py
Examines multicast traffic from WSJT-X. When TX mode is intiated, the DX callsign and grid square are read. If the grid square is present it will be set the DX station grid square in HamClock via the API. If the grid square is NOT present in WSJT-X, a QRZ lookup will be preformed, and the DX station grid will be set in HamClock. Also, the script will send the callsign 3 times to the WinKeyer Server to be played on CW sidetone.

This script depends upon WSJTXClass.py which you can get at: https://github.com/rstagers/WSJT-X/blob/master/WSJTXClass.py

