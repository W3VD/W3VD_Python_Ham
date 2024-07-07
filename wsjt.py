import socket
import struct
import subprocess
import requests
import xml.etree.ElementTree as ET

# Import the WSJT-X classes https://github.com/rstagers/WSJT-X/blob/master/WSJTXClass.py
from WSJTXClass import WSJTX_Packet, WSJTX_Heartbeat, WSJTX_Status, WSJTX_Decode, WSJTX_Erase, WSJTX_Reply, WSJTX_Logged, WSJTX_Closed, WSJTX_Replay, WSJTX_HaltTx, WSJTX_FreeText, WSJTX_WSPRDecode

# WSJT multicast address and port. In WSJT go to: File, settings, reporting tab, change UDP server from 127.0.0.1 to 224.0.2.0. Select your network adapater in outgoing interfaces.
WSJThost = "224.0.2.0"
WSJTport = 2237 # No quote marks, this must be seen as an INT data type

QRZlookupEnable = True
QRZusername = "QRZuser"
QRZpassword = "QRZpass"

HAMclockEnable = True
HAMclockHost = "192.168.3.52"
HAMclockPort = "8080"

WinKeyerEnable = True
WinKeyerHost = "127.0.0.1"
WinKeyerPort = 7373 # No quote marks, this must be seen as an INT data type
WordSpeed = "25"
CharacterSpeed = "25"

# Function to decode packets
def decode_packet(data):
    pkt = WSJTX_Packet(data, 0)
    pkt.Decode()

    if pkt.PacketType == 0:
        pkt = WSJTX_Heartbeat(data, pkt.index)
    elif pkt.PacketType == 1:
        pkt = WSJTX_Status(data, pkt.index)
    elif pkt.PacketType == 2:
        pkt = WSJTX_Decode(data, pkt.index)
    elif pkt.PacketType == 3:
        pkt = WSJTX_Erase(data, pkt.index)
    elif pkt.PacketType == 4:
        pkt = WSJTX_Reply(data, pkt.index)
    elif pkt.PacketType == 5:
        pkt = WSJTX_Logged(data, pkt.index)
    elif pkt.PacketType == 6:
        pkt = WSJTX_Closed(data, pkt.index)
    elif pkt.PacketType == 7:
        pkt = WSJTX_Replay(data, pkt.index)
    elif pkt.PacketType == 8:
        pkt = WSJTX_HaltTx(data, pkt.index)
    elif pkt.PacketType == 9:
        pkt = WSJTX_FreeText(data, pkt.index)
    elif pkt.PacketType == 10:
        pkt = WSJTX_WSPRDecode(data, pkt.index)

    try:
        pkt.Decode()
    except:
        thing = False
    return pkt.__dict__

def get_key():

    url = f"https://xmldata.qrz.com/xml/current/?username={QRZusername};password={QRZpassword}"
    response = requests.get(url)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        namespaces = {'qrz': 'http://xmldata.qrz.com'}  # Define namespaces
        key_element = root.find("./qrz:Session/qrz:Key", namespaces)  # Use namespaces in XPath
        if key_element is not None:
            key = key_element.text
            return key
        else:
            print("Key element not found in XML.")
            return None
    else:
        print(f"Failed to retrieve key. Status code: {response.status_code}")
        return None

def get_grid_square(call_sign,):
    key = get_key()
    url = f"https://xmldata.qrz.com/xml/current/?s={key};callsign={call_sign}"
    response = requests.get(url)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        namespaces = {'qrz': 'http://xmldata.qrz.com'}
        grid_element = root.find("./qrz:Callsign/qrz:grid", namespaces)
        if grid_element is not None:
            grid_square = grid_element.text
            return grid_square
        else:
            print("Grid square not found in XML.")
            return None
    else:
        print(f"Failed to retrieve grid square. Status code: {response.status_code}")
        return None

def send_message(host, port, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(message.encode('ascii'))
            print(f"Sent: {message}")
    except Exception as e:
        print(f"Failed to send message: {e}")

# Main function to receive and decode multicast packets
def main():
    multicast_group = WSJThost
    server_address = ('', WSJTport)

    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to the server address
    sock.bind(server_address)

    # Tell the operating system to add the socket to the multicast group
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    call_worked = ''

    while True:
        data, address = sock.recvfrom(10240)
        packet = decode_packet(data)
        try:
            transmitting = bool(packet['Transmitting'])
        except:
            transmitting = False

        try:
            if transmitting:
                grid = packet['DXgrid']
                call = packet['DXCall']
                if call_worked != call:
                    call_worked = call
                    print(packet)
                    if WinKeyerEnable:
                        send_message(WinKeyerHost, WinKeyerPort, f"{WordSpeed}{CharacterSpeed} {call} {call} {call} ")
                    if HAMclockEnable:
                        if len(grid) < 4 and QRZlookupEnable:
                            grid = get_grid_square(call)
                            print(f"QRZ grid: {grid}")
                        if len(grid) >= 4:                        
                            url = f"http://{HAMclockHost}:{HAMclockPort}/set_newdx?grid={grid}"
                            subprocess.Popen(['curl', url])
        except:
            thing = False

if __name__ == '__main__':
    main()
