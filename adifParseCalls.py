import adif_io # pip install adif_io

input_file_path = '/home/brenden/Downloads/w3vd.79689.20240616221238.adi'
output_file_path = '/home/brenden/cw/calls.txt'

def parse_adif_qsos(file_path):
    with open(file_path, 'r', encoding='latin-1') as file:
        adif_string = file.read()

    qsos, header = adif_io.read_from_string(adif_string)

    parsed_calls = []

    for qso in qsos:
        parsed_calls.append(qso['CALL'])
    return parsed_calls

parsed_records = parse_adif_qsos(input_file_path)

with open(output_file_path, 'w') as f:
    f.write("\n".join(map(str, list(set(parsed_records)))))