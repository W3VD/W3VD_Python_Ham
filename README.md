All of these scripts require Python v3.6 or later. These scripts are designed to be cross platform compatible. Despite its name, the K1EL WinKeyer will work with Linux and Mac systems in addition to Windows.

# winKeyerServer.py

Interfaces with a K1EL WinKeyer. Creates a TCP server that other hosts on your network can send messages to be played on sidetone. Each message sent to the WinKeyer includes its own WPM and Farnsworth Character speed. Also echos paddle presses back to the host, which are sent to the network via multicast, for the purpose of grading accuracy during sending practice. This is not intended to send CW live on the radio. These tools are intended only to be used with a WinKeyer that is keying an AF code practice oscillator. Another use case for this server is to recieve alerts. For example, a future use case I have in mind is when CW skimmer decodes one of my buddies on the air, or a spotted POTA station, it would play their call sign.

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
On Linux you may need dialout permissions. I did this on Debian with:
```bash
sudo usermod -aG dialout your_username
```
# Prosigns
The K1EL WinKeyer has several prosigns mapped directly to ASCII characters. See page 15 of https://www.k1elsystems.com/files/WinkeyUSBman.pdf for more information.

The BK Prosign unfortunately is not currently mapped in the WinKeyer firmware. winKeyerClient.py and morseCodePractice.py have both been configured, so that when the unmapped ASCII character "&" is sent, the WinKeyer command used for making custom prosigns is used and BK will be played correctly. However, because this is not mapped in the WinKeyer firmware, sending BK on the paddle will result in the character "#" to be echoed back, indicating an unsuccessful decode by the WinKeyer. Hopefully one day K1EL will decide to add BK as a mapped prosign, perhaps more folks contacting him about this will provide encouragement.

Prosign  | WinKeyer ASCII | Flex CWX ASCII
:---: | :---: | :---:
AR | < | +
BK | not mapped | &
BT | = | =
KN | : | (
SK | > | $

# winKeyerClient.py

Used to test the WinKeyer Server, or just play a desired message at a desired speed when you wish. Set the IP and port as appropriate in the script to match that of the TCP port of the WinKeyer Server. Run the script with no paramters. First 4 digits of the message must include the two digit word speed followed by the two digit character speed. For example, if you wanted to send "CQ CQ DE W3VD K" at 5 WPM word speed with a 15 WPM character speed you would enter:
```bash
0515CQ CQ DE W3VD K
```

# morseCodePractice.py

Uses the WinKeyer Server for copy and sending practice. Takes input from a text file with one character/word/message per line. For copy practice the message will be played on sidetone, and expected to be typed back via the computer keyboard. If the student wants to hear the message again they may press the backslash key "\\". For sending practice you have the option of displaying text on the screen and/or playing the message on sidetone. The student is expected to send the message using the paddle attached to the WinKeyer.

For copy or send practice the script will keep track of the amount of times the student gets the message correct on the first try. Final results, and the settings used for each session are stored in CSV files. History.csv will contain cumulative results and settings used for each session. Another CSV file is saved for each session containing scores for each specific message. 

Copy practice, send with a word speed of 15, character speed of 25, with a count of 20 repetitions:
```bash
python morseCodePractice.py -w 15 -F 25 -c 20 -f ~/cw/char.txt
```

Send practice, same as above except the -p option is used to enable paddle input. When no count is specified it will play all the messages in the file one time:
```bash
python morseCodePractice.py -w 15 -F 25 -p 1 -f ~/cw/pota.txt
```

Default options may be set by editing the vars at the top of the file. Command line options may also be used to change behavior. These can be listed by :
```bash
python morseCodePractice.py --help
```

Before first time use, the user MUST set the desired Log Directory variable in the script.

# adifParseCalls.py
This script reads an ADIF format log file and exports a unique list of callsigns to a text file, for use as an input file to morseCodePractice.py. You will need to edit the input and output file variables in the script.

Python module adif_io is required, you can install with: 
```bash
pip install adif_io
```

# wsjt.py

Examines multicast traffic from WSJT-X. When TX mode is intiated, the DX callsign and grid square are read. If the grid square is present, it will set the DX station grid square in HamClock via the API. If the grid square is NOT present in WSJT-X, a QRZ lookup will be preformed, and the DX station grid will be set in HamClock. Also, the script will send the callsign 3 times to the WinKeyer Server to be played on CW sidetone.

This script depends upon WSJTXClass.py which you can get at: https://github.com/rstagers/WSJT-X/blob/master/WSJTXClass.py

Python module requests is required, you can install with: 
```bash
pip install requests
```

WSJT-X must be setup for multicast, this allows any host on your subnet to read the traffic. Go to File, settings, reporting tab, change UDP server from 127.0.0.1 to 224.0.2.0. Any valid multicast address may be used instead of 224.0.2.0. You will have to configure any software such as Gridtracker, etc to listen to the same multi cast address instead of 127.0.0.1.

Edit the variables at the top of the file as appropriate.
