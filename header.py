import socket
import time
from struct import *
from socket import *
import sys

TIMEOUT = 0.5

# Header format
header_format = '!IIHH'

handshake_complete = False
global_seq_num = 1
global_ack_num = 1


def create_packet(seq_num, ack_num, flags, window_size, data):
    header = pack(header_format, seq_num, ack_num, flags, window_size)
    packet = header + data
    return packet


def parse_header(header):
    header_from_msg = unpack(header_format, header)
    return header_from_msg


def parse_flags(flags):
    syn = (flags >> 3) & 1
    ack = (flags >> 2) & 1
    fin = (flags >> 1) & 1

    return syn, ack, fin


def send(sock, data, seq_num, addr):
    packet = create_packet(seq_num, 0, 0, 0, data)
    #print("Sent packet with seq_num", seq_num)

    sock.sendto(packet, addr)
    #return seq_num


def send_ack(sock, ack_num, addr):
    ack_msg = create_packet(0, ack_num, 4, 64, b'')
    sock.sendto(ack_msg, addr)


def stop_and_wait(sock, addr, data):
    """
    Implements the Stop_and_Wait protocol for reliable data transfer over UDP

    Arguments:
        sock (socket): The UDP socket object
        addr (Tuple): A tuple containing the IP address and port number of the remote host
        data (bytes): The data to be sent

    Returns:
        None
    """

    # Declare global variables that will be modified within this function
    global global_seq_num
    global handshake_complete

    # If handshake has not yet been completed, establish connection
    if not handshake_complete:
        flags = 8   # 1 0 0 0 = SYN flag value
        syn_packet = create_packet(0, 0, flags, 0, b'')     # Create SYN packet
        sock.sendto(syn_packet, addr)   # Send SYN packet to destination address
        print("Sent SYN packet with seq_num", 0)

        received_synack = False
        while not received_synack:
            # Set a timeout of 0.5 seconds for the socket for receiving SYN-ACK message
            sock.settimeout(0.5)
            try:
                synack_msg, addr = sock.recvfrom(1472)  # Receive message from the destination address
                header_from_msg = synack_msg[:12]   # Extract the header from the received message
                seq_num, ack_num, flags, win = parse_header(header_from_msg)    # Parse the header fields
                syn, ack, fin = parse_flags(flags)  # Parse the flags

                # If received SYN-ACK message is valid, send final ACK packet and complete handshake
                if syn and ack and not fin:
                    print("Received SYN-ACK msg with ak_num", ack_num)
                    flags = 4   # 0 1 0 0 = ACK flag value
                    ack_packet = create_packet(0, 0, flags, 0, b'')     # Create final ACK packet
                    sock.sendto(ack_packet, addr)   # Send ACK to destination address
                    print("Sent final ACK packet with ack_num", 0)
                    handshake_complete = True   # Set handshake_complete  to True
                    received_synack = True  # Set received_synack to True

            # If timeout occurs, resend SYN packet
            except timeout:
                print(f"Timeout occurred. Resending SYN packet with seq_num 0")
                flags = 8   # 1 0 0 0 = SYN flag value
                syn_packet = create_packet(0, 0, flags, 0, b'')     # Create new SYN packet
                sock.sendto(syn_packet, addr)   # Send new SYN packet to destination address

    # Once handshake is complete, send data packets and wait for ACKs
    send(sock, data, global_seq_num, addr)  # Send first data packet with current sequence number

    # Wait for ACK message from the receiver
    received_ack = False
    while not received_ack:
        # Set a timeout og 0.5 seconds for the socket for receiving ACK message

        try:
            ack_msg, addr = sock.recvfrom(1472)     # Receive message from destination address
            header_from_msg = ack_msg[:12]  # Extract the header from the received message
            seq_num, ack_num, flags, win = parse_header(header_from_msg)    # Parse the header fields
            syn, ack, fin = parse_flags(flags)  # Parse the flags

            # If received ACK message is valid, update global sequence number and set received_ack to True
            if ack and ack_num == global_seq_num:
                print(f"ACK msg: ack_num={ack_num}, flags={flags}")
                global_seq_num += 1
                received_ack = True

            # Else if received duplicate ACK message
            elif ack and ack_num == global_seq_num - 1:
                print("Received duplicate ACK msg with ack_num", ack_num)
                send(sock, data, global_seq_num - 1, addr)

            else:
                sock.settimeout(0.5)

        except timeout:
            print(f"Timeout occurred. Resending packet with seq_num={global_seq_num}, flags=0")
            send(sock, data, global_seq_num, addr)


def receive(sock, test):
    global handshake_complete
    if not handshake_complete:
        received_final_ack = False
        while not received_final_ack:

            try:
                syn_packet, addr = sock.recvfrom(1472)
                header = syn_packet[:12]
                syn, ack, fin = parse_flags(parse_header(header)[2])

                if syn and not ack and not fin:
                    print("Received SYN msg")
                    syn_ack_msg = create_packet(0, 0, 12, 64, b'')
                    sock.sendto(syn_ack_msg, addr)

                elif not syn and ack and not fin:
                    print("Received final ACK msg")
                    handshake_complete = True
                    received_final_ack = True

            except Exception as e:
                print("Error:", e)
                sys.exit()

    global global_ack_num
    while True:
        msg, addr = sock.recvfrom(1472)

        header_from_msg = msg[:12]
        seq_num, ack_num, flags, win = parse_header(header_from_msg)
        syn, ack, fin = parse_flags(flags)

        if test:
            time.sleep(1)

        if not fin and not syn and not ack and seq_num == global_ack_num:
            print(f"Received packet with seq_num", seq_num)
            app_data = msg[12:]
            send_ack(sock, global_ack_num, addr)
            #ack_msg = create_packet(0, global_ack_num, flags, win, b'')

            #sock.sendto(ack_msg, addr)
            #print("Sent ACK msg with ack_num", self_ack_num)

            global_ack_num = seq_num + 1

            return app_data

        # Usikker om man skal resende ACK melding til forrige packet hvis man får det igjen
        '''elif not fin and not syn and not ack and seq_num == global_ack_num - 1:
            print(f"Received duplicate packet with seq_num", seq_num)

            flags = 4
            send_ack(sock, global_ack_num - 1, addr)
            #ack_msg = create_packet(0, global_ack_num - 1, flags, win, b'')

            #sock.sendto(ack_msg, addr)'''

        if fin and not ack and not syn and seq_num == global_ack_num:
            print("FIN msg received with seq_num", seq_num)
            flags = 4
            send_ack(sock, global_ack_num, addr)
            #fin_ack_msg = create_packet(0, global_ack_num, flags, win, b'')
            #sock.sendto(fin_ack_msg, addr)

            global_ack_num = seq_num + 1
            sock.close()
            return


def close_conn(sock, addr):
    global global_seq_num

    flags = 2
    fin_msg = create_packet(global_seq_num, 0, flags, 0, b'')
    sock.sendto(fin_msg, addr)

    fin_ack_received = False
    while not fin_ack_received:
        sock.settimeout(0.5)
        try:
            fin_ack_msg, addr = sock.recvfrom(1472)
            header_from_msg = fin_ack_msg[:12]
            seq_num, ack_num, flags, win = parse_header(header_from_msg)
            syn, ack, fin = parse_flags(flags)

            if ack and ack_num == global_seq_num:
                print("Received ACK msg for FIN msg with ack_num", ack_num)
                global_seq_num += 1
                sock.close()
                fin_ack_received = True
                return

            elif not ack and ack_num < global_seq_num:
                print("Received duplicate ACK msg with ack_num", ack_num)
                flags = 2
                fin_msg = create_packet(global_seq_num, 0, flags, 0, b'')
                sock.sendto(fin_msg, addr)
        except timeout:
            print(f"Timeout occurred. Resending FIN msg")
            sock.sendto(fin_msg, addr)

def go_back_n(sock, addr, data):
    global  global_seq_num
    window_size = 5
    base = 1

    while base < global_seq_num:
        for i in range(base, min(base + window_size, global_seq_num + 1)):
            send(sock, data, global_seq_num, addr)
            global_seq_num += 1

        try:
            while True:
                ack_msg = sock.recvfrom(1472)
                header_from_msg = ack_msg[:12]
                seq_num, ack_num, flags, win = parse_header(header_from_msg)
                syn, ack, fin = parse_flags(flags)
                print("Received ACK msg with ack_num", ack_num)

                if ack_num >= base:
                    base = ack_num + 1
                    window_size = min(window_size + (base - global_seq_num))

        except timeout:
            print("Timeout - retrasnmitting packet with seq_num", global_seq_num)


def receive_gbn(sock):
    global global_ack_num

    while True:
        packet, addr = sock.recvfrom(1472)
        header_from_packet = packet[:12]
        seq_num, ack_num, flags, win = parse_header(header_from_packet)
        syn, ack, fin = parse_flags(flags)

        if seq_num == global_ack_num:
            print("Received packet with seq_num", seq_num)
            data = packet[12:]
            flags = 4
            ack_msg = create_packet(0, global_ack_num, flags, win, b'')

            sock.sendto(ack_msg, addr)

            global_ack_num += 1
            return data


'''
class DRTP:
    def __init__(self, sock,dst_ip, dst_port, reliable_method):
        self.seq_num = 1
        self.ack_num = 1
        self.window_size = 64
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.reliable_method = reliable_method
        self.sock = sock
        self.handshake_complete = False

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

    def initiate_handshake(self):
        # Step 1: Send SYN packet
        seq_num = 1
        syn_packet = self.create_packet(seq_num, 0, 8, 0, b'')
        self.sock.sendto(syn_packet, (self.dst_ip, self.dst_port))
        print("Sent SYN msg")

        # Step 2: Wait for SYN-ACK packet
        # sock.settimeout(0.5)
        # expected_ack = 1
        expected_ack = seq_num + 1
        try:
            while True:
                data, addr = self.sock.recvfrom(1472)
                header = data[:12]
                seq_num, ack_num, flags, win = self.parse_header(header)
                syn, ack, fin = self.parse_flags(flags)
                if syn and ack and ack_num == expected_ack:
                    print("Received SYN_ACK msg")
                    print(f"SYN_ACK_NRs: seq={seq_num}, ack_nr={ack_num}, flags={flags}, win={win}")
                    # SYN-ACK packet received, send ACK packet
                    seq_num += 1
                    ack_num = self.parse_header(header)[0]
                    flags = 4
                    ack_packet = self.create_packet(seq_num, ack_num, flags, 0, b'')
                    self.sock.sendto(ack_packet, addr)
                    print("Sent ACK msg")
                    self.handshake_complete = True
                    # expected_ack += 1

        except timeout:
            # Timeout waiting for SYN-ACK, retry handshake
            self.sock.settimeout(0.5)
            return None

    def handle_handshake(self):
        # Step 1: Wait for SYN packet
        while True:
            data, addr = self.sock.recvfrom(1472)
            header = data[:12]
            seq_num, ack_num, flags, win = self.parse_header(header)
            syn, ack, fin = self.parse_flags(flags)
            if syn and not ack:
                print("Received SYN msg")
                print(f"SYN_NRs: seq={seq_num}, ack_nr={ack_num}, flags={flags}, win={win}")
                # SYN packet received, send SYN-ACK packet
                flags = 12
                win = 64

                syn_ack_packet = self.create_packet(0, seq_num + 1, flags, win, b'')
                self.sock.sendto(syn_ack_packet, addr)
                print("Sent SYN_ACK msg")

            elif ack and not syn:
                print("Received final ACK msg")
                print(f"ACK_NRs: seq={seq_num}, ack_nr={ack_num}, flags={flags}, win={win}")
                self.handshake_complete = True

    def send(self, data):
        if not self.handshake_complete:
            return
        packet = self.create_packet(self.seq_num, 0, 0, self.window_size, data)
        #print("Sent packet with seq_num", self.seq_num)

        self.sock.sendto(packet, (self.dst_ip, self.dst_port))
        #return self.seq_num


    def stop_and_wait(self, data):
        if not self.handshake_complete:
            flags = 8
            syn_packet = self.create_packet(1, 0, flags, 0, b'')
            self.sock.sendto(syn_packet, (self.dst_ip, self.dst_port))
            print("Sent SYN packet with seq_num", self.seq_num)

            received_synack = False
            while not received_synack:
                self.sock.settimeout(0.5)
                try:
                    synack_msg, addr = self.sock.recvfrom(1472)
                    header_from_msg = synack_msg[:12]
                    seq_num, ack_num, flags, win = self.parse_header(header_from_msg)
                    syn, ack, fin = self.parse_flags(flags)

                    if syn and ack and not fin:
                        print("Received SYN-ACK msg with ak_num", ack_num)
                        flags = 4
                        ack_packet = self.create_packet(0, 1, flags, 0, b'')
                        self.sock.sendto(ack_packet, addr)
                        print("Sent final ACK packet with ack_num", 1)
                        self.handshake_complete = True
                        received_synack = True

                    elif syn and ack and not fin:
                        print("Resending SYN msg with seq_num")
                        syn_packet = self.create_packet(seq_num+1, 0, flags, 0, b'')
                        self.sock.sendto(syn_packet, (self.dst_ip, self.dst_port))


                except timeout:
                    print(f"Timeout occurred. Resending SYN packet with seq_num {self.seq_num}")
                    syn_packet = self.create_packet(self.seq_num, 0, flags, 0, b'')
                    self.sock.sendto(syn_packet, (self.dst_ip, self.dst_port))

        self.send(data)

        received_ack = False
        while not received_ack:
            self.sock.settimeout(0.5)
            try:
                ack_msg, addr = self.sock.recvfrom(1472)
                header_from_msg = ack_msg[:12]
                seq_num, ack_num, flags, win = self.parse_header(header_from_msg)
                syn, ack, fin = self.parse_flags(flags)

                if ack and ack_num == self.seq_num + 1:
                    print("Received ACK msg with ack_num", ack_num)
                    self.seq_num += 1
                    received_ack = True

                elif ack and ack_num == self.seq_num:
                    print("Received duplicate ACK msg with ack_num", ack_num)
                    self.send(data)

            except timeout:
                print(f"Timeout occurred. Resending packet with seq_num", self.seq_num)
                self.send(data)


    def receive(self):

        if not self.handshake_complete:
            received_final_ack = False
            while not received_final_ack:

                try:
                    syn_packet, addr = self.sock.recvfrom(1472)
                    header = syn_packet[:12]
                    syn, ack, fin = self.parse_flags(self.parse_header(header)[2])

                    if syn and not ack and not fin:
                        print("Received SYN msg")
                        synack_msg = self.create_packet(0, 1, 12, 64, b'')
                        self.sock.sendto(synack_msg, addr)

                    elif not syn and ack and not fin:
                        print("Received final ACK msg")
                        self.handshake_complete = True
                        received_final_ack = True

                except Exception as e:
                    print("Error:", e)
                    sys.exit()

        while True:
            msg, addr = self.sock.recvfrom(1472)

            header_from_msg = msg[:12]
            seq_num, ack_num, flags, win = self.parse_header(header_from_msg)
            print(f"Received packet with seq_num", seq_num)

            if seq_num == self.ack_num:
                app_data = msg[12:]
                flags = 4
                self.ack_num = seq_num + 1

                ack_msg = self.create_packet(0, self.ack_num, flags, win, b'')
                self.sock.sendto(ack_msg, addr)
                #print("Sent ACK msg with ack_num", self.ack_num)
                return app_data
                '''

