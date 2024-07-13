import adif_io
import argparse
import os

default_US_State = "FL"
default_Park_prefix = "US-"
default_Output_Directory = "/home/brenden/pota_logs"

# Process command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help = "Input File")
parser.add_argument("-o", "--output", help = "Output Directory")
parser.add_argument("-a", "--activated", help = 'Activated multiple parks, accepts comma delimited list. Example: python pota_log.py -m "1234,4321"')
parser.add_argument("-s", "--state", help = "Activated State")
args = parser.parse_args()
if args.input:
    input_file_path = args.input
    if not os.path.isfile(input_file_path):
        print("Input file does not exist")
        exit()
else:
    print("Must specify input file")
    exit()
if args.output:
    default_Output_Directory = args.output
else:
    if not os.path.exists(default_Output_Directory):
        print("Output directory does not exist")
        exit()
if args.activated:
    activated_parks = args.activated.split(',')
else:
    activated_parks = ""
if args.state:
    default_US_State = args.state

# Functions
def create_adif_record(station_callsign, operator, call, qso_date, time_on, band, mode, submode, my_sig, my_sig_info, sig, sig_info, my_state):
    record = f"<STATION_CALLSIGN:{len(station_callsign)}>{station_callsign} " \
             f"<OPERATOR:{len(operator)}>{operator} " \
             f"<CALL:{len(call)}>{call} " \
             f"<QSO_DATE:{len(qso_date)}>{qso_date} " \
             f"<TIME_ON:{len(time_on)}>{time_on} " \
             f"<BAND:{len(band)}>{band} " \
             f"<MODE:{len(mode)}>{mode} " \
             f"<SUBMODE:{len(submode)}>{submode} " \
             f"<MY_SIG:{len(my_sig)}>{my_sig} " \
             f"<MY_SIG_INFO:{len(my_sig_info)}>{my_sig_info} " \
             f"<SIG:{len(sig)}>{sig} " \
             f"<SIG_INFO:{len(sig_info)}>{sig_info} " \
             f"<MY_STATE:{len(my_state)}>{my_state}" \
             "<EOR>\n"
    return record

def parse_adif_qsos(file_path, my_park):
    with open(file_path, 'r', encoding='latin-1') as file:
        adif_string = file.read()
    qsos, header = adif_io.read_from_string(adif_string)

    parsed_qsos = ""

    for qso in qsos:
        station_callsign = qso.get('STATION_CALLSIGN', '')
        operator = qso.get('OPERATOR', '')
        call = qso.get('CALL', '')
        qso_date = qso.get('QSO_DATE', '')
        time_on = qso.get('TIME_ON', '')
        band = qso.get('BAND', '')
        mode = qso.get('MODE', '')
        submode = qso.get('SUBMODE', '')
        my_sig = qso.get('MY_SIG', '')
        my_sig_info = qso.get('MY_SIG_INFO', '')        
        sig = qso.get('SIG', '')
        sig_info = qso.get('SIG_INFO', '')
        my_state = qso.get('MY_STATE', '')

        if len(my_park) > 0:
            my_sig_info = my_park
        if len(operator) == 0:
            operator = station_callsign
        if len(my_state) == 0:
            my_state = default_US_State        

        if len(sig_info) > 0:
            parks = sig_info.split(',')
            for park in parks:
                if len(park) < 7:
                    park = f"{default_Park_prefix}{park}"
                if len(park) == 7 or len(park) == 8:
                    park = park.upper()
                    parsed_qsos = parsed_qsos + create_adif_record(station_callsign,operator,call,qso_date,time_on,band,mode,submode,my_sig,my_sig_info,sig,park,my_state)
                else:
                    print(f"Park length not equal to 7 or 9: {call} {park}")
                    exit()
        else:
            parsed_qsos = parsed_qsos + create_adif_record(station_callsign,operator,call,qso_date,time_on,band,mode,submode,my_sig,my_sig_info,sig,sig_info,my_state)
    
    return parsed_qsos

# Start logic
adif_header = """https://github.com/W3VD/W3VD_Python_Ham/blob/main/pota_log.py
<adif_ver:3>1.0
<programid:16>W3VD POTA script
<programversion:3>1.0
<eoh>\n"""

if len(activated_parks) > 0:
    for activated_park in activated_parks:
        if len(activated_park) < 7:
            activated_park = f"{default_Park_prefix}{activated_park}"
        if len(activated_park) == 7 or len(activated_park) == 8:
            activated_park = activated_park.upper()      
            output_file_path = os.path.join(default_Output_Directory,f"{os.path.splitext(os.path.basename(input_file_path))[0]}_{activated_park}_POTA.adi")
            adif_content = adif_header + parse_adif_qsos(input_file_path, activated_park)
            with open(output_file_path, 'w', encoding='latin-1') as file:
                file.write(adif_content)
        else:
            print(f"Activated park length not equal to 7 or 9: {activated_park}")
            exit()
else:
    output_file_path = os.path.join(default_Output_Directory,f"{os.path.splitext(os.path.basename(input_file_path))[0]}_POTA.adi")
    adif_content = adif_header + parse_adif_qsos(input_file_path, "")
    with open(output_file_path, 'w', encoding='latin-1') as file:
        file.write(adif_content)
