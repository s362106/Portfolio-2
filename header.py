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
    seq_num = 1
    ack_num = 0
    flags = 8
    window_size = 0
    syn_packet = create_packet(seq_num, ack_num, flags, window_size, b'')
    sock.sendto(syn_packet, (dest_addr, dest_port))
    print("Sent SYN msg")

    # Step 2: Wait for SYN-ACK packet
    #sock.settimeout(0.5)
    #expected_ack = 1
    try:
        while True:
            data, addr = sock.recvfrom(1472)
            header = data[:12]
            seq, ack_nr, flags, win = parse_header(header)
            syn, ack, fin = parse_flags(flags)
            if syn and ack:
                print("Received SYN_ACK msg")
                print(f"SYN_ACK_NRs: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                # SYN-ACK packet received, send ACK packet
                seq_num += 1
                ack_num = parse_header(header)[0]
                flags = 4
                ack_packet = create_packet(seq_num, ack_num, flags, 0, b'')
                sock.sendto(ack_packet, addr)
                print("Sent ACK msg")
                #expected_ack += 1
                return True
    except socket.timeout:
        # Timeout waiting for SYN-ACK, retry handshake
        sock.settimeout(None)
        return start_handshake(sock, dest_addr, dest_port)


def handle_handshake(sock):
    # Step 1: Wait for SYN packet
    seq_num = -1
    while True:
        data, addr = sock.recvfrom(1472)
        header = data[:12]
        seq, ack_nr, flags, win = parse_header(header)
        syn, ack, fin = parse_flags(flags)
        if syn and not ack:
            print("Received SYN msg")
            print(f"SYN_NRs: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
            # SYN packet received, send SYN-ACK packet
            seq_num += 1
            ack_num = parse_header(header)[0]
            flags = 12
            win = 64

            syn_ack_packet = create_packet(seq_num, ack_num, flags, win, b'')
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
            ack_packet = create_packet(seq_num, ack_num, flags, win, data)
            sock.sendto(ack_packet, addr)
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