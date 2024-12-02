import gpsd
from geopy.geocoders import Nominatim
import maidenhead as mh
import adif_io
import argparse
import os
from datetime import datetime, timezone
import csv
import re

server = '192.168.73.3'
default_Output_Directory = "C:\\Users\\brenden.BKM\\Documents\\POTA_logs"

# Process command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help = "Required: Input File")
parser.add_argument("-c", "--calls", help = 'Required: Operator List, accepts comma delimited list. Example: python pota_log.py -m "W3VD,W6XRL4"')
parser.add_argument("-o", "--output", help = "Optional: Output Directory")
parser.add_argument("-a", "--activated", help = 'Optional: Activated multiple parks, accepts comma delimited list. Example: python pota_log.py -a "1234,4321"')
parser.add_argument("-l", "--lat", help = "Optional: Lattitude")
parser.add_argument("-L", "--lon", help = 'Optional: Longitude')

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
if not os.path.exists(default_Output_Directory):
    print("Output directory does not exist")
    exit()
if args.calls:
    station_callsign_list = args.calls.split(',')
    if len(station_callsign_list) == 0:
        print("No call signs specified")
        exit()
else:
    print("Must specify input file")
    exit()

# Dictionary to map state names to their abbreviations
STATE_ABBREVIATIONS = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA',
    'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT',
    'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}

# Mapping state abbreviations to ITU zones with longitude considerations
ITU_ZONE_MAPPING = {
    'CT': 8, 'ME': 8, 'MA': 8, 'NH': 8, 'RI': 8, 'VT': 8,
    'NJ': 8, 'NY': 8, 'DE': 8, 'MD': 8, 'PA': 8, 'AL': 8,
    'FL': 8, 'GA': 8, 'NC': 8, 'SC': 8, 'TN': 8, 'VA': 8,
    'OH': 8, 'WV': 8, 'MI': (8, 7, -90), 'KY': 8,
    'IL': (8, 7, -90), 'IN': 8, 'WI': (8, 7, -90),
    'AR': (8, 7, -90), 'LA': (8, 7, -90), 'MS': (8, 7, -90),
    'MO': (8, 7, -90), 'TX': 7, 'OK': 7, 'NM': 7, 'CO': 7,
    'IA': 7, 'KS': 7, 'MN': 7, 'MT': (7, 6, -110),
    'NE': 7, 'ND': 7, 'SD': 7, 'WY': 7, 'AZ': (7, 6, -110),
    'NV': 6, 'ID': 6, 'OR': 6, 'WA': 6, 'CA': 6,
    'UT': (7, 6, -110)
}

# Mapping state abbreviations to CQ zones
CQ_ZONE_MAPPING = {
    # Zone 3
    'AZ': 3, 'ID': 3, 'NV': 3, 'OR': 3, 'UT': 3, 'WA': 3, 'CA': 3,
    # Zone 4
    'MT': 4, 'WY': 4, 'CO': 4, 'NM': 4, 'TX': 4, 'OK': 4, 'KS': 4,
    'NE': 4, 'SD': 4, 'ND': 4, 'IA': 4, 'MN': 4, 'MO': 4, 'AR': 4,
    'LA': 4, 'WI': 4, 'IL': 4, 'MI': 4, 'IN': 4, 'OH': 4, 'WV': 4,
    'KY': 4, 'TN': 4, 'AL': 4, 
    # Zone 5
    'CT': 5, 'ME': 5, 'MA': 5, 'NH': 5, 'RI': 5, 'VT': 5,
    'NJ': 5, 'NY': 5, 'DE': 5, 'MD': 5, 'PA': 5, 'FL': 5,
    'GA': 5, 'NC': 5, 'SC': 5, 'VA': 5, 'WV': 5
}

adif_header = """https://github.com/W3VD/W3VD_Python_Ham/blob/main/gpsd_log.py
<adif_ver:3>1.0
<programid:16>W3VD Rover Script
<programversion:3>1.0
<eoh>\n"""

csv_header = ['UTCdateTime', 'Lat', 'Lon', 'Grid', 'State', 'County', 'CQzone', 'ITUzone', 'POTA_parks', 'LoTW_file']

def get_gps_data(server):
    try:
        gpsd.connect(host=server)
        packet = gpsd.get_current()
        lat = packet.lat
        lon = packet.lon
        return lat, lon
    except Exception as e:
        print(f"Error connecting to GPSD server: {e}")
        return None, None

def get_gridsquare(lat, lon):
    return mh.to_maiden(lat, lon)

def get_location_info(lat, lon):
    try:
        geolocator = Nominatim(user_agent="gpsd_script")
        location = geolocator.reverse((lat, lon), exactly_one=True, language="en")
        if location and 'address' in location.raw:
            address = location.raw['address']
            state = address.get('state', 'Unknown')
            county = address.get('county', 'Unknown')
            county = county.replace(" County", "") if county else "Unknown"
            state_abbr = STATE_ABBREVIATIONS.get(state, 'Unknown')
            return state_abbr, county
        else:
            return None, None
    except:
        return None, None

def calculate_itu_zone(state_abbr, lon):
    zone_info = ITU_ZONE_MAPPING.get(state_abbr)
    if isinstance(zone_info, tuple):
        zone_east, zone_west, lon_divide = zone_info
        return zone_east if lon > lon_divide else zone_west
    return zone_info

def calculate_cq_zone(state_abbr):
    return CQ_ZONE_MAPPING.get(state_abbr, None)

def calculate_prefix(call_sign):
    # Call sign prefix extraction using regex
    match = re.match(r'^([A-Z0-9]+)', call_sign)
    
    if match:
        prefix = match.group(1)
        
        # Adjust prefix based on some common rules
        # Example: US callsigns have 1 or 2 letters followed by a digit
        if len(prefix) >= 2 and prefix[1].isdigit():
            return prefix[:2]  # e.g., K1ABC -> K1
        elif len(prefix) >= 3 and prefix[2].isdigit():
            return prefix[:3]  # e.g., ZS6XYZ -> ZS6
        
        return prefix  # Default case if no other rules apply
    else:
        return None

def create_adif_record(station_callsign, operator, my_state, my_cnty, MY_LAT, MY_LON, MY_GRIDSQUARE, MY_CQ_ZONE, MY_ITU_ZONE, call, qso_date, time_on, band, freq, mode, submode, cont, country, DXCC, CQz, ITUz, Pfx, RST_Sent, RST_Rcvd):
    if station_callsign == call:
        
        if len(station_callsign_list) == 2:        
            call = next(item for item in station_callsign_list if item != station_callsign)
            Pfx = calculate_prefix(call)

    record = f"<STATION_CALLSIGN:{len(station_callsign)}>{station_callsign} " \
             f"<OPERATOR:{len(operator)}>{operator} " \
             f"<MY_STATE:{len(my_state)}>{my_state} " \
             f"<MY_CNTY:{len(my_cnty)}>{my_cnty} " \
             f"<MY_LAT:{len(MY_LAT)}>{MY_LAT} " \
             f"<MY_LON:{len(MY_LON)}>{MY_LON} " \
             f"<MY_GRIDSQUARE:{len(MY_GRIDSQUARE)}>{MY_GRIDSQUARE} " \
             f"<MY_CQ_ZONE:{len(MY_CQ_ZONE)}>{MY_CQ_ZONE} " \
             f"<MY_ITU_ZONE:{len(MY_ITU_ZONE)}>{MY_ITU_ZONE} " \
             f"<CALL:{len(call)}>{call} " \
             f"<QSO_DATE:{len(qso_date)}>{qso_date} " \
             f"<TIME_ON:{len(time_on)}>{time_on} " \
             f"<FREQ:{len(freq)}>{freq} " \
             f"<BAND:{len(band)}>{band} " \
             f"<MODE:{len(mode)}>{mode} " \
             f"<SUBMODE:{len(submode)}>{submode} " \
             f"<RST_SENT:{len(RST_Sent)}>{RST_Sent} " \
             f"<RST_RCVD:{len(RST_Rcvd)}>{RST_Rcvd} " \
             f"<CONT:{len(cont)}>{cont} " \
             f"<COUNTRY:{len(country)}>{country} " \
             f"<DXCC:{len(DXCC)}>{DXCC} " \
             f"<CQZ:{len(CQz)}>{CQz} " \
             f"<ITUZ:{len(ITUz)}>{ITUz} " \
             f"<PFX:{len(Pfx)}>{Pfx}" \
             "<EOR>\n"
    return record

def parse_adif_qsos(file_path, operator_call, my_state, my_cnty, MY_LAT, MY_LON, MY_GRIDSQUARE, MY_CQ_ZONE, MY_ITU_ZONE):
    with open(file_path, 'r', encoding='latin-1') as file:
        adif_string = file.read()
    qsos, header = adif_io.read_from_string(adif_string)

    parsed_qsos = ""

    for qso in qsos:
        call = qso.get('CALL', '')
        qso_date = qso.get('QSO_DATE', '')
        time_on = qso.get('TIME_ON', '')
        band = qso.get('BAND', '')
        mode = qso.get('MODE', '')
        submode = qso.get('SUBMODE', '')
        freq = qso.get('FREQ', '')
        cont = qso.get('CONT', '')
        country = qso.get('COUNTRY', '')
        dxcc = qso.get('DXCC', '')
        CQz = qso.get('CQZ', '')
        ITUz = qso.get('ITUZ', '')
        Pfx = qso.get('PFX', '')
        RST_Sent = qso.get('RST_SENT', '')
        RST_Rcvd = qso.get('RST_RCVD', '')
        parsed_qsos = parsed_qsos + create_adif_record(operator_call, operator_call, my_state, my_cnty, str(MY_LAT), str(MY_LON), MY_GRIDSQUARE, str(MY_CQ_ZONE), str(MY_ITU_ZONE), call, qso_date, time_on, band, freq, mode, submode, cont, country, dxcc, CQz, ITUz, Pfx, RST_Sent, RST_Rcvd)
    return parsed_qsos

def append_to_csv(file_name, row_data, header=None):
    # Check if the file exists
    file_exists = os.path.isfile(file_name)
    
    # Open the file in append mode
    with open(file_name, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write the header if the file does not exist
        if not file_exists and header:
            writer.writerow(header)
        
        # Write the data row
        writer.writerow(row_data)

# Start Script logic
if args.lat and args.lon:
    lat = float(args.lat)
    lon = float(args.lon)
else:
    lat, lon = get_gps_data(server)
    
if lat is not None and lon is not None:
    print(f"Latitude: {lat}, Longitude: {lon}")
    gridsquare = get_gridsquare(lat, lon)
    print(f"Gridsquare: {gridsquare}")
    state_abbr, county = get_location_info(lat, lon)
        
    if state_abbr and county:
        print(f"State: {state_abbr}, County: {county}")
    else:
        print("Could not determine state and county.")
        
    itu_zone = calculate_itu_zone(state_abbr, lon)
    cq_zone = calculate_cq_zone(state_abbr)

    if itu_zone:
        print(f"ITU Zone: {itu_zone}")
    else:
        print("Could not determine ITU zone.")
        
    if cq_zone:
        print(f"CQ Zone: {cq_zone}")
    else:
        print("Could not determine CQ zone.")
else:
    print("Failed to retrieve GPS data.")

print(f"Input File: {input_file_path}")
print(f"Callsigns: {station_callsign_list}")
print(f"Parks activated: {args.activated}")
print("")

# Prompt the user for confirmation
user_input = input("Is the data correct? Enter 'y' to continue: ")

# Check if the user pressed 'y'
if user_input.lower() == 'y':
    now_utc = datetime.now(timezone.utc)
    utc_YYYY_MM_DD = str(now_utc.strftime('%Y-%m-%d'))
    formatted_datetime = now_utc.strftime('%Y-%m-%d %H:%M:%S')
    for call in station_callsign_list:
        output_dir = os.path.join(default_Output_Directory,call,utc_YYYY_MM_DD)
        cummulative_log = os.path.join(output_dir,f"{call}-{utc_YYYY_MM_DD}.adi")
        lotw_log = os.path.join(output_dir,f"{os.path.splitext(os.path.basename(input_file_path))[0]}_{call}_LoTW.adi")
        csv_file = os.path.join(output_dir,f"Locations_{call}.csv")

        parsed_adif_qsos = parse_adif_qsos(input_file_path, call, state_abbr, f"{state_abbr},{county}", lat, lon, gridsquare, cq_zone, itu_zone)
        lotw_qsos = adif_header + parsed_adif_qsos

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(cummulative_log):
            with open(cummulative_log, 'w', encoding='latin-1') as file:
                file.write(adif_header)

        csv_row = [formatted_datetime, lat, lon, gridsquare, state_abbr, county, cq_zone, itu_zone, args.activated, f"{os.path.splitext(os.path.basename(input_file_path))[0]}_{call}_LoTW.adi"]
        append_to_csv(csv_file, csv_row, csv_header)

        with open(cummulative_log, 'a', encoding='latin-1') as file:
            file.write(parsed_adif_qsos)                
        with open(lotw_log, 'w', encoding='latin-1') as file:
            file.write(lotw_qsos)
        
        if args.activated:
            os.system(f"python pota_log.py -i {input_file_path} -o {output_dir} -a {args.activated} -m {call} -s {state_abbr} -g {args.calls}")
else:
    exit()
