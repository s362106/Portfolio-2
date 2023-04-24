from struct import  *

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



'''sequence_nr = 1
acknowledgement_nr = 0
window = 0
flags = 0

data = bytes(1460)

msg = create_packet(sequence_nr, acknowledgement_nr, window, flags, data)

header_from_msg = msg[:12]
print('Header form message length:',len(header_from_msg))

seq, ack, flags, win = parse_header(header_from_msg)

data_from_msg = msg[12:]
print('Data length:',len(data_from_msg))


data = b''
print('\n\nCreating an aknowledgment pakcet:')
print(f'This is an empty packet with no data = {len(data)}')

sequence_nr = 0
acknowledgement_nr = 1
window = 0

flags = 4

msg = create_packet(sequence_nr, acknowledgement_nr, flags, window, data)
print(f'This is an aknowledgement packet of size {len(msg)}')

seq, ack, flags, win = parse_header(msg)
print(f'seq={seq}, ack={ack}, flags={flags}, receiver-window={win}')

syn, ack, fin = parse_flags(flags)
print (f'syn_flag = {syn}, ack_flag={ack}, and fin_flag={fin}')'''



'''from socket import *
import sys
import struct

class DRTP:
    def __init__(self, seq_num, ack_num, syn_flag, ack_flag, fin_flag, reset_flag, window_size):

        self.seq_num = seq_num
        self.ack_num = ack_num
        self.syn_flag = syn_flag
        self.ack_flag = ack_flag
        self.fin_flag = fin_flag
        self.reset_flag = reset_flag
        self.window_size = window_size

    # This function packs inputed values into a header
    def pack(self):
        # Pack the TCP header fields into a binary string
        try:
            flags = (self.syn_flag << 3) | (self.ack_flag << 2) | (self.fin_flag << 1) | (self.reset_flag)

            # L = 4 bytes, H = 2 bytes, ! = big-endian
            drtp_header = struct.pack('!LLHH', self.seq_num, self.ack_num, flags, self.window_size)
            return drtp_header
        except struct.error as e:
            print("Error packing DRTPHeader:", e)
            return None

    # This function unpacks inputed values
    @classmethod
    def unpack(cls, packed_data):
        # Unpack a binary string into TCP header fields
        try:
            seq_num, ack_num, flags, window_size = struct.unpack('!LLHH', packed_data)
            syn_flag = (flags >> 3) & 1
            ack_flag = (flags >> 2) & 1
            fin_flag = (flags >> 1) & 1
            reset_flag = flags & 1
            return cls(seq_num, ack_num, syn_flag, ack_flag, fin_flag, reset_flag, window_size)
        except struct.error as e:
            print("Error unpacking DRTPHeader:", e)
            return None
'''