import serial
import socket
import threading
import struct
import argparse

# pip install pyserial
# On linux you will need dial out permissions: sudo usermod -aG dialout your_username

DefaultPort = '/dev/ttyUSB0' # Windows uses format 'COM7' 
DefaultWordSpeed = 25 # Minimum value 5
DefaultCharacterSpeed = 25 # Minimum value 10
IncomingTCPhost = '0.0.0.0'
IncomingTCPport = 7373
PaddleSendMulticastHost = '224.0.2.73'
PaddleSendMulticastPort = 7373

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", help = "WinKeyer Serial Port")
args = parser.parse_args()
if args.port:
    port = args.port
else:
    port = DefaultPort

PaddleSend = False # Inializing a var, do not modify

class WinKeyer:
    def __init__(self, serial_device):
        self.port = serial.Serial(
            port=serial_device,
            baudrate=1200,
            stopbits=serial.STOPBITS_TWO,
            timeout=1,
            rtscts=False,
            dsrdtr=False,
            bytesize=serial.EIGHTBITS
        )
        self.port.setDTR(True)
        self.port.setRTS(False)
        self.host_open()

    def host_open(self):
        self.port.write((chr(0x0) + chr(0x2)).encode())
        version = ord(self.port.read(1))
        if version not in (23, 30, 31):
            raise Exception(f"Unsupported WinKeyer version: {version}")
        self.port.write(b'\x0E\x44') # Enable Serial and Paddle echo
        self.port.write((chr(0x5) + chr(5) + chr(94) + chr(255)).encode())

    def host_close(self):
        self.port.write((chr(0x0) + chr(0x3) + chr(0x43)).encode())

    def send(self, msg):
        self.port.write(msg.upper().encode())

    def set_speed(self, speed):
        assert 5 <= speed <= 99
        self.port.write((chr(0x2) + chr(speed)).encode())

    def set_farns(self, speed):
        assert 10 <= speed <= 99
        self.port.write((chr(0xD) + chr(speed)).encode())

    def process_winkey_byte(self, wkbyte):
        global PaddleSend
        if (wkbyte & 0xc0) == 0xc0:
            if wkbyte == 198:
                PaddleSend = True
            if wkbyte == 192:
                PaddleSend = False
        elif (wkbyte & 0xc0) == 0x80:
            pass
        else:
            # Convert the echo byte to human-readable character
            CharSent = chr(wkbyte)
            print(CharSent, end='', flush=True)
            if PaddleSend:
                send_multicast_message(CharSent)

    def read_char(self):
        if self.port.in_waiting > 0:
            wkbyte = ord(self.port.read(1))
            self.process_winkey_byte(wkbyte)
        else:            
            pass

def handle_client(client_socket, winkeyer):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            RAWmessage = data.decode('ascii')
            WPM = int(RAWmessage[:2])
            Farnsworth = int(RAWmessage[2:4])
            message = RAWmessage[4:]
            winkeyer.set_speed(WPM)
            winkeyer.set_farns(Farnsworth)
            winkeyer.send(message)
            print(f"WPM: {str(WPM)} Farnsworth: {str(Farnsworth)}")
            print(message)
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

def start_server(host, port, winkeyer):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")
    
    try:
        while True:
            client_socket, addr = server.accept()
            print("")
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket, winkeyer))
            client_handler.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()
        winkeyer.host_close()

def read_winkeyer(winkeyer):
    try:
        while True:
            winkeyer.read_char()
    except KeyboardInterrupt:
        print("Stopping character reading...")

def send_multicast_message(message: str, multicast_address: str = PaddleSendMulticastHost, port: int = PaddleSendMulticastPort):
    if not message or len(message) != 1:
        raise ValueError("Message must be a single ASCII character.")
    
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # Set the TTL (time-to-live) for messages to 1 so they do not go past the local network segment
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    
    # Send the message
    sock.sendto(message.encode('ascii'), (multicast_address, port))

if __name__ == "__main__":
    winkeyer = WinKeyer(port)
    winkeyer.set_speed(DefaultWordSpeed)
    winkeyer.set_farns(DefaultCharacterSpeed)
    
    reader_thread = threading.Thread(target=read_winkeyer, args=(winkeyer,))
    reader_thread.daemon = True
    reader_thread.start()
    
    start_server(IncomingTCPhost, IncomingTCPport, winkeyer)
