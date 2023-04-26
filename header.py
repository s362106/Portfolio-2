import time
from struct import  *
from socket import *
import sys

TIMEOUT = 0.5

# Header format
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


def start_handshake(sock, dest_addr, dest_port):
    # Step 1: Send SYN packet
    syn_packet = create_packet(seq=0, ack=0, flags=4, win=0, data=b'')
    sock.sendto(syn_packet, (dest_addr, dest_port))

    # Step 2: Wait for SYN-ACK packet
    sock.settimeout(0.5)
    expected_ack = 1
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            header = data[:12]
            seq, ack_nr, flags, win = parse_header(header)
            syn, ack, fin = parse_flags(flags)
            if syn == 1 and ack and ack_nr == expected_ack:
                # SYN-ACK packet received, send ACK packet
                ack_packet = create_packet(seq+1, seq, 0, 0, b'')
                sock.sendto(ack_packet, addr)
                expected_ack += 1
                break
    except socket.timeout:
        # Timeout waiting for SYN-ACK, retry handshake
        sock.settimeout(None)
        return start_handshake(sock, dest_addr, dest_port)

    # Step 3: Wait for ACK packet
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            header = data[:12]
            seq, ack, flags, win = parse_header(header)
            syn, ack, fin = parse_flags(flags)
            if ack == 1:
                # ACK packet received, handshake complete
                sock.settimeout(None)
                return True
    except socket.timeout:
        # Timeout waiting for ACK, retry handshake
        sock.settimeout(None)
        return start_handshake(sock, dest_addr, dest_port)


def handle_handshake(sock, src_addr, src_port):
    # Step 1: Wait for SYN packet
    while True:
        data, addr = sock.recvfrom(1472)
        header = data[:12]
        seq, ack, flags, win = parse_header(header)
        syn, ack, fin = parse_flags(flags)
        if syn == 1 and ack == 0:
            # SYN packet received, send SYN-ACK packet
            seq = 0
            flags = 12
            win = 64
            syn_ack_packet = create_packet(seq, seq, flags, win, b'')
            sock.sendto(syn_ack_packet, addr)
            break

    # Step 2: Wait for ACK packet
    while True:
        data, addr = sock.recvfrom(1024)
        header = data[:12]
        seq, ack, flags, win = parse_header(header)
        syn, ack, fin = parse_flags(flags)
        if ack == 1:
            # ACK packet received, handshake complete
            return True


def send_packet(client_sock, addr, file_path):

    print("Opening file")
    try:
        file = open(file_path, 'rb')
    except IOError as e:
        print("Failed to open file. Error:", e)
        sys.exit()

    expected_ack = 0

    seq = 0

    while True:
        data = file.read(1460)

        ack_nr = 0
        win = 0
        flags = 0

        if not data:
            flags = 2
            data = b''
            fin_packet = create_packet(seq, ack_nr, flags, win, data)

            client_sock.sendto(fin_packet, addr)
            break

        else:
            packet = create_packet(seq, ack_nr, flags, win, data)
            client_sock.sendto(packet, addr)

            client_sock.settimeout(0.5)
            received_acks = []
            while True:
                client_sock.settimeout(0.5)
                try:
                    ack_packet, addr = client_sock.recvfrom(1472)
                    seq, ack_nr, flags, win = parse_header(ack_packet)
                    syn, ack, fin = parse_flags(flags)

                    if ack and ack_nr == expected_ack:
                        print(f"Received ACK for packet", ack_nr)
                        received_acks.append(ack_nr)

                        break

                    elif ack_nr < expected_ack:
                        print(f"Received a duplicate ACK for packet {ack_nr}")
                        if ack_nr not in received_acks:
                            received_acks.append(ack_nr)
                            break

                except timeout:
                    client_sock.sendto(packet, addr)

            seq += 1
            expected_ack += 1

    client_sock.close()