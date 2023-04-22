from socket import *
import sys
import struct

class DRTPHeader:
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
