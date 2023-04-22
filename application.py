from socket import *
import time
import ipaddress
import argparse
import sys
import threading
import re
import struct


# Define the simplified TCP header structure
class TCPSimpleHeader:
    def __init__(self, seq_num, ack_num, syn_flag, ack_flag, fin_flag, reset_flag, window_size):

        self.seq_num = seq_num
        self.ack_num = ack_num
        self.syn_flag = syn_flag
        self.ack_flag = ack_flag
        self.fin_flag = fin_flag
        self.reset_flag = reset_flag
        self.window_size = window_size

    def pack(self):
        # Pack the TCP header fields into a binary string
        flags = (self.syn_flag << 3) | (self.ack_flag << 2) | (self.fin_flag << 1) | (self.reset_flag)

        tcp_header = struct.pack('!LLHH',

                                 self.seq_num,
                                 self.ack_num,
                                 flags,
                                 self.window_size)
        return tcp_header

    @classmethod
    def unpack(cls, packed_data):
        # Unpack a binary string into TCP header fields
        seq_num, ack_num, flags, window_size= struct.unpack('!LLHH', packed_data)
        syn_flag = (flags >> 3) & 1
        ack_flag = (flags >> 2) & 1
        fin_flag = (flags >> 1) & 1
        reset_flag = flags & 1
        return cls(seq_num, ack_num, syn_flag, ack_flag, fin_flag, reset_flag, window_size)


def checkIP(address):
    try:
        ip = ipaddress.IPv4Address(address)

    except:
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-p', '--port', type=int, help='Port number to listen on')
    parser.add_argument('-b', '--bind', type=str)

    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')



