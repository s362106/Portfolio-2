import socket
import time
from struct import *
from socket import *
import sys

TIMEOUT = 0.5

# Header format
header_format = '!IIHH'



class DRTP:
    def __init__(self):
        self.seq_num = 0
        self.ack_num = 0
        self.flags = 0
        self.window_size = 64

    def create_packet(self, seq_num, ack_num, flags, window_size, data):
        header = pack(header_format, seq_num, ack_num, flags, window_size)
        packet = header + data
        return packet

    def parse_header(self, header):
        header_from_msg = unpack(header_format, header)
        return header_from_msg

    def parse_flags(self, flags):
        syn = (flags >> 3) & 1
        ack = (flags >> 2) & 1
        fin = (flags >> 1) & 1

        return syn, ack, fin

    def initiate_handshake(self, sock, dest_addr, dest_port):
        # Step 1: Send SYN packet
        seq_num = 1
        ack_num = 0
        flags = 8
        window_size = 0
        syn_packet = self.create_packet(seq_num, ack_num, flags, window_size, b'')
        sock.sendto(syn_packet, (dest_addr, dest_port))
        print("Sent SYN msg")

        # Step 2: Wait for SYN-ACK packet
        # sock.settimeout(0.5)
        # expected_ack = 1
        try:
            while True:
                data, addr = sock.recvfrom(1472)
                header = data[:12]
                seq, ack_nr, flags, win = self.parse_header(header)
                syn, ack, fin = self.parse_flags(flags)
                if syn and ack:
                    print("Received SYN_ACK msg")
                    print(f"SYN_ACK_NRs: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                    # SYN-ACK packet received, send ACK packet
                    seq_num += 1
                    ack_num = self.parse_header(header)[0]
                    flags = 4
                    ack_packet = self.create_packet(seq_num, ack_num, flags, 0, b'')
                    sock.sendto(ack_packet, addr)
                    print("Sent ACK msg")
                    # expected_ack += 1
                    return True
        except socket.timeout:
            # Timeout waiting for SYN-ACK, retry handshake
            sock.settimeout(None)
            return self.initiate_handshake(sock, dest_addr, dest_port)

    def handle_handshake(self, sock):
        # Step 1: Wait for SYN packet
        seq_num = -1
        while True:
            data, addr = sock.recvfrom(1472)
            header = data[:12]
            seq, ack_nr, flags, win = self.parse_header(header)
            syn, ack, fin = self.parse_flags(flags)
            if syn and not ack:
                print("Received SYN msg")
                print(f"SYN_NRs: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                # SYN packet received, send SYN-ACK packet
                seq_num += 1
                ack_num = self.parse_header(header)[0]
                flags = 12
                win = 64

                syn_ack_packet = self.create_packet(seq_num, ack_num, flags, win, b'')
                sock.sendto(syn_ack_packet, addr)
                print("Sent SYN_ACK msg")

            elif ack and not syn:
                print("Received final ACK msg")
                print(f"ACK_NRs: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                ack_num = seq
                seq_num += 1
                flags = 4
                win = 64
                data = b''
                ack_packet = self.create_packet(seq_num, ack_num, flags, win, data)
                sock.sendto(ack_packet, addr)
                return True


    def stop_and_wait(self, sock, dest_ip, dest_port, data):

        seq_num = self.seq_num
        ack_num = 0
        flags = 0
        window_size = 0

        packet = self.create_packet(seq_num, ack_num, flags, window_size, data)
        print(f"Sent data packet: seq_num={seq_num}, ack_num={ack_num}, flags={flags}, win={window_size}")

        ack_received = False
        while not ack_received:
            try:
                sock.sendto(packet, (dest_ip, dest_port))
                sock.settimeout(0.5)
                ack_packet, addr = sock.recvfrom(1472)
                header = self.parse_header(ack_packet[:12])
                seq_num, ack_num, flags, window_size = self.parse_header(header)
                syn, ack, fin = self.parse_flags(flags)

                if ack and ack_num == self.seq_num:
                    print("ACK received for sequence number:", ack_num)
                    self.ack_num += 1
                    ack_received = True

                elif ack and ack_num == self.seq_num - 1:
                    print("Duplicate ACK for sequence number:", ack_num)
                    sock.sendto(packet, (dest_ip, dest_port))

                else:
                    print("ACK not received for sequence_number:", seq_num)
                    sock.sendto(packet, (dest_ip, dest_port))

            except socket.timeout:
                print("Timeout occurred, resending packet with sequence number:", seq_num)
                sock.sendto(packet, (dest_ip, dest_port))


    def receive_data(self, sock, packet, src_ip, src_port):

        header_from_msg = packet[:12]
        data = packet[12:]

        seq_num, ack_num, flags, window_size = self.parse_header(header_from_msg)
        syn, ack, fin = self.parse_flags(flags)

        if seq_num == self.ack_num:
            self.ack_num += 1

            ack_flag = 4
            window_size = 64

            ack_packet = self.create_packet(self.seq_num, self.ack_num, ack_flag, window_size, b'')
            sock.sendto(ack_packet, (src_ip, src_port))

            return data

        else:
            print("Unexpected sequence number, discarding packet:", seq_num)
            ack_flag = 4
            window_size = 64

            print("Sending ACK for sequence number:", self.ack_num - 1)
            ack_packet = self.create_packet(self.seq_num, self.ack_num - 1, ack_flag, window_size, b'')
            sock.sendto(ack_packet, (src_ip, src_port))


        try:
            while True:
                data, addr = sock.recvfrom(1472)
                header = data[:12]
                self.seq_num, self.ack_num, self.flags, self.window_size = self.parse_header(header)
                syn, ack, fin = self.parse_flags(self.flags)
                if not syn and not ack:
                    print(f"Received data packet: seq_num={self.seq_num}, ack_num={self.ack_num}, flags={self.flags}, win={self.window_size}")
                    # Data packet received, send ACK packet
                    self.seq_num = ack
                    self.ack_num = self.seq_num
                    self.flags = 4
                    ack_packet = self.create_packet(self.seq_num, self.ack_num, self.flags, self.window_size, data)
                    sock.sendto(ack_packet, addr)
                    print(f"Self.seq_num={self.seq_num}, self.ack_num={self.ack_num}")
                    return data[12:]

        except Exception as e:
            print("Error:", e)
            return None


    '''def stop_and_wait(self, sock, dest_addr, packet):
        ack_received = False
        while not ack_received:
            try:
                sock.sendto(packet, dest_addr)
                print("Packet sent")

                sock.settimeout(0.5)
                data, addr = sock.recvfrom(1472)

                ack_seq_num, ack_ack_num, ack_flags, ack_window_size = self.parse_header(data[:12])
                ack_syn, ack_ack, ack_fin = self.parse_flags(ack_flags)

                if ack_ack_num == self.seq_num and ack_ack:
                    print("Ack received")
                    ack_received = True

                else:
                    print("Duplicate ack received, resending packet")
                    sock.sendto(packet, dest_addr)

            except socket.timeout:
                print("Timeout occurred, resending packet")
                sock.sendto(packet, dest_addr)'''
