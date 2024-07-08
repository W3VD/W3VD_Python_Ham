#! /bin/python3
import socket
import struct
import random
import time
import sys
import argparse
import csv
import os
from datetime import datetime

# Default values
InputFile = '/home/brenden/cw/char.txt'
LogDirectory = "/home/brenden/cw/logs"
WPM = "20"
Farnsworth = "20"
EnforceSpace = False
PaddleInput = False
DisplayText = False
SoundText = True
TXserver_host = '127.0.0.1'
TXserver_port = 7373
RXserver_host = '224.0.2.73'
RXserver_port = 7373
RemoveStringFromList = True

boolean_dict = {"true": True, "t": True, "yes": True, "y": True, "1": True, "false": False,"f": False,  "no": False,"n": False, "0": False}

# Initialize parser
parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("-f", "--file", help = "Input File")
parser.add_argument("-c", "--MaxCount", help = "Maximum count of repetitions")
parser.add_argument("-w", "--wpm", help = "Character Speed WPM")
parser.add_argument("-F", "--Farnsworth", help = "Farnsworth character speed")
parser.add_argument("-p", "--PaddleInput", help = "Paddle Input True/False. If False Keyboard will be used Default False")
parser.add_argument("-r", "--RemoveStringFromList", help = "True/False. If true, as each message is used, it is removed from the list and not will not repeated until the list is exhausted. Default value is True.")
parser.add_argument("-S", "--EnforceSpace", help = "Enforce space when sending with paddle")
parser.add_argument("-t", "--DisplayText", help = "Display message text on screen")
parser.add_argument("-s", "--SoundText", help = "Play message text via WinKeyer")
parser.add_argument("-th", "--TXserver_host", help = "Winkeyer Server TX host")
parser.add_argument("-tp", "--TXserver_port", help = "Winkeyer Server TX port")
parser.add_argument("-rh", "--RXserver_host", help = "Paddle Multicast IP")
parser.add_argument("-rp", "--RXserver_port", help = "Paddle Multicast port")

# Read arguments from command line
args = parser.parse_args()

if args.file:
    InputFile = args.file
if args.wpm:    
    WPM = args.wpm
if args.Farnsworth:
    Farnsworth = args.Farnsworth    
if args.PaddleInput:
    PaddleInput = boolean_dict.get(args.PaddleInput.lower())
    DisplayText = True
    SoundText = False
if args.EnforceSpace:
    EnforceSpace = boolean_dict.get(args.EnforceSpace.lower())
if args.DisplayText:
    DisplayText = boolean_dict.get(args.DisplayText.lower())
if args.SoundText:
    SoundText = boolean_dict.get(args.SoundText.lower())
if args.RemoveStringFromList:
    RemoveStringFromList = boolean_dict.get(args.RemoveStringFromList.lower())
if args.TXserver_host:
    TXserver_host = args.TXserver_host
if args.TXserver_port:
    TXserver_port = int(args.TXserver_port)
if args.RXserver_host:
    RXserver_host = args.RXserver_host
if args.RXserver_port:
    RXserver_port = int(args.RXserver_port)

if not DisplayText and not SoundText:
    print("Error: Must set DisplayText and/or SoundText var to True")
    exit()

if len(WPM) == 1:
    WPM = f"0{WPM}"
if len(Farnsworth) == 1:
    WPM = f"10"

if WPM > Farnsworth:
    print("Error: Farnsworth must be greater then WPM")
    exit()

if sys.platform.startswith('win'):
    import msvcrt

    def getch():
        return msvcrt.getch().decode('utf-8')
else:
    import tty
    import termios

    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch    

def load_strings_from_file(file_path):
    my_list = []
    with open(file_path, 'r') as file:
        for line in file:
            my_list.append(line.strip().upper())
    return my_list

def listen_multicast_message(multicast_address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    mreq = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    while True:
        data, _ = sock.recvfrom(1024)
        yield data.decode('ascii')

def send_message(message,host, port):
    message = f"{WPM}{Farnsworth}{message}"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(message.encode('ascii'))
    except Exception as e:
        print(f"Failed to send message: {e}")

def create_dict_from_file(file_path):
    my_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            key = line.strip()
            my_dict[key] = [0, 0]
    return my_dict

def export_dict_to_csv(dictionary, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the header
        header = ['Message', 'Sent', 'Correct']
        writer.writerow(header)
        
        # Write the dictionary items
        for key, value in dictionary.items():
            # Ensure value has exactly two elements
            if len(value) != 2:
                raise ValueError(f"Value for key '{key}' does not have exactly 2 elements.")
            row = [key] + value
            writer.writerow(row)

def main(filename):
    Count = 0
    CorrectCount = 0
    strings = load_strings_from_file(filename)
    strings_dict = create_dict_from_file(filename)
    if args.MaxCount:
        MaxCount = int(args.MaxCount)
    else:
        MaxCount = len(strings)
    listener = listen_multicast_message(RXserver_host,RXserver_port)
    send_message(" ", TXserver_host, TXserver_port)

    while Count < MaxCount:
        time.sleep(1)
        CorrectFirstTime = True
        if len(strings) == 0:
            strings = load_strings_from_file(filename)
        target_string = random.choice(strings).upper()
        target_string_sent = strings_dict[target_string][0]
        target_string_correct = strings_dict[target_string][1]
        target_string_spaces = target_string

        if not EnforceSpace:
            target_string = target_string.replace(" ","")
            
        if DisplayText:   
            print(f"Message: {target_string_spaces}")
        if SoundText:
            send_message(target_string, TXserver_host, TXserver_port)
        
        matched_chars = ""
        if PaddleInput:
            for incoming_char in listener:
                if incoming_char == " ":
                    if EnforceSpace:
                        matched_chars += incoming_char
                else: 
                    matched_chars += incoming_char

                if matched_chars == target_string[:len(matched_chars)]:
                    if len(matched_chars) == len(target_string):
                        print("Correct!")
                        break
                else:
                    if DisplayText:
                        print(f"Mismatch! Expected message: {target_string_spaces}")
                    if SoundText:
                        time.sleep(0.5)
                        send_message(target_string, TXserver_host, TXserver_port)
                    matched_chars = ""
                    CorrectFirstTime = False
        else:
            CorrectAnswer = False
            while not CorrectAnswer:
                if len(target_string) == 1:
                    KeyboardInput = getch()
                else:
                    KeyboardInput = input("Enter message: ")

                if KeyboardInput.upper() == target_string:
                    print("Correct!")
                    CorrectAnswer = True
                else:
                    if KeyboardInput == '\\' and SoundText:
                        time.sleep(0.5)
                        send_message(target_string, TXserver_host, TXserver_port)
                    else:
                        if DisplayText:
                            print(f"Mismatch! Expected message: {target_string_spaces}")
                        else:
                            print("Mismatch!")
                        if SoundText:
                            time.sleep(0.5)
                            send_message(target_string, TXserver_host, TXserver_port)
                        matched_chars = ""
                        CorrectFirstTime = False

        Count = Count + 1
        if RemoveStringFromList:
            strings.remove(target_string_spaces)
        if CorrectFirstTime:
            CorrectCount = CorrectCount + 1
            strings_dict[target_string_spaces] = [(target_string_sent+1),(target_string_correct+1)]
        else:
            strings_dict[target_string_spaces] = [(target_string_sent+1),(target_string_correct)]
    
    percentCorrect = round(((CorrectCount/Count)*100),1)
    print(f"{percentCorrect}% {CorrectCount} out of {Count} Correct")
    
    # Export file
    if not os.path.exists(LogDirectory): 
        os.makedirs(LogDirectory)

    HistoryFile = os.path.join(LogDirectory,"history.csv")
    if not os.path.exists(HistoryFile):
        with open(HistoryFile, 'w') as f:
            f.write("DateTime,InputFile,PracticeType,WPM,Farnsworth,Count,Correct,Percent,CSVfile\n")

    current_unix_time = int(time.time())
    PracticeType = 'copy'
    if PaddleInput:
        PracticeType = 'send'
    csv_file = f"{current_unix_time}-{PracticeType}.csv"
    file_path_out = os.path.join(LogDirectory,csv_file)
    export_dict_to_csv(strings_dict, file_path_out)

    with open(HistoryFile, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{filename},{PracticeType},{str(WPM)},{str(Farnsworth)},{str(Count)},{str(CorrectCount)},{str(percentCorrect)},{file_path_out}\n")

if __name__ == "__main__":
    main(InputFile)
