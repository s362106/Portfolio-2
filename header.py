from struct import  *

# Define the header format
header_format = '!IIHH'
def create_packet(seq, ack, flags, win, data):
    header = pack(header_format, seq, ack, flags, win)

    packet = header + data

    #print(f'Packet containing header + data of size {len(packet)}')

    return packet


def parse_header(header):
    header_from_msg = unpack(header_format, header)
    return header_from_msg


def parse_flags(flags):
    syn = (flags >> 3) & 1
    ack = (flags >> 2) & 1
    fin = (flags >> 1) & 1

    return syn, ack, fin