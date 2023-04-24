from socket import *
import time
import ipaddress
import argparse
import sys
import threading
import re
import struct
from drtp import *

BUFFER_SIZE = 1472


# Define the simplified TCP header structure


def run_server(ip, port):
    file_path = 'received_file.png'
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))
        server_socket.settimeout(0.5)

        print(f"Server listening on {ip}:{port}")

    except Exception as e:
        print("Failed to bind. Error:", e)
        sys.exit()

    print("Performing three-way handshake")

    expected_seq = 0

    while True:
        syn_packet, addr = server_socket.recvfrom(BUFFER_SIZE)
        syn_header = syn_packet[:12]
        seq, ack_nr, flags, win = parse_header(syn_header)
        syn, ack, fin = parse_flags(flags)

        if syn and not ack:
            print("Received SYN message")
            sequence_nr = 0
            ack_nr = seq + 1
            flags = 12

            SYN_ACK = create_packet(sequence_nr, ack_nr, flags, 0, b'')

            server_socket.sendto(SYN_ACK, addr)
            print("Sent SYN-ACK message")

        elif not syn and ack:
            print("Received final ACK message")
            break

    with open(file_path, 'wb') as file:
        while True:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
            header_msg = data[:12]
            msg = data[12:]

            seq, ack_nr, flags, win = parse_header(header_msg)

            syn, ack, fin = parse_flags(flags)
            print(f"Header values seq={seq}, ack={ack}, and fin={fin}")


            file.write(msg)


            if fin:
                ack_nr = seq +1
                flags = 6
                packet = create_packet(seq, ack_nr, flags, 0, b'')

                server_socket.sendto(packet, addr)
                break


def run_client(server_ip, server_prt):
    try:
        client_sock = socket(AF_INET, SOCK_DGRAM)

    except Exception as e:
        print("Failed to send data. Error:", e)
        sys.exit()

    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 20.15.05.png'

    print("Åpner filen")
    file = open(file_path, 'rb')

    sequence_number = 0
    data = b''
    ack_nr = 0
    win = 64
    flags = 8
    syn_packet = create_packet(sequence_number, ack_nr, flags, win, data)
    client_sock.sendto(syn_packet, (server_ip, server_prt))

    handshake_complete = False
    while not handshake_complete:
        syn_ack_packet, addr = client_sock.recvfrom(BUFFER_SIZE)
        seq, ack_nr, flags, win = parse_header(syn_ack_packet[:12])
        syn, ack, fin = parse_flags(flags)

        if ack and syn and ack_nr == sequence_number + 1:
            print("Received SYN-ACK message")
            ack_nr = sequence_number + 1
            flags = 4
            sequence_number += 1

            ack_packet = create_packet(sequence_number, ack_nr, flags, win, data)
            client_sock.sendto(ack_packet, addr)
            print("Sent ACK message")
            handshake_complete = True


    while True:
        data = file.read(1460)

        if not data:
            print("Sender FIN message")
            flags = 2
            data = b''
            packet = create_packet(sequence_number, 0, flags, 64, data)

            client_sock.sendto(packet, (server_ip, server_prt))
            break

        packet = create_packet(seq=sequence_number, ack=0, flags=0, win=0, data=data)
        client_sock.sendto(packet, (server_ip, server_prt))
        sequence_number += 1
    client_sock.close()
    '''sequence_nr = 0
    acknowledgement_nr = 0
    window = 64
    flags = 8
    data = b''
    SYN = create_packet(sequence_nr, acknowledgement_nr, flags, window, data)

    client_sock.sendto(SYN, (server_ip, server_prt))
    print("Sent SYN message")

    while True:
        print("Receiving data")
        server_packet, addr = client_sock.recvfrom(BUFFER_SIZE)
        header = server_packet[:12]

        seq, ack, flags, win = parse_header(header)
        print("Window size is:", win)

        syn, ack, fin = parse_flags(flags)
        print(f"Header values seq={syn}, ack={ack}, and fin={fin}")

        # ACK
        if syn == 1 and ack == 1:
            print("Received SYN-ACK message")
            data = b''
            sequence_nr = 1
            acknowledgement_nr = seq + 1
            window = 64
            flags = 4
            ACK = create_packet(sequence_nr, acknowledgement_nr, flags, window, data)

            client_sock.sendto(ACK, addr)
            print("Sent ACK message")'''



'''def run_server(ip, port):
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))

        print(f"Server listening on {ip}:{port}")

    except Exception as e:
        print("Failed to bind. Error:", e)
        sys.exit()

    file_path = 'received_file.txt'

    with open(file_path, 'wb') as file:
        while True:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)

            if not data:
                break

            file.write(data)


    server_socket.close()

def run_client(server_ip, server_prt):
        try:
            client_sock = socket(AF_INET, SOCK_DGRAM)

        except Exception as e:
            print("Failed to send data. Error:", e)
            sys.exit()

        file_path = '/Users/fahmimohammed/fil.txt'

        file = open(file_path, 'rb')
        while True:

            file_data = file.read(1460)

            if not file_data:
                break

            sequence_nr = 0
            acknowledgement_nr = 0
            window = 64
            flags = 0
            header = create_packet(sequence_nr, acknowledgement_nr, flags, window, file_data)

            client_sock.sendto(header, (server_ip, server_prt))

        file.close()
        client_sock.close()'''

def check_ip(address):
    try:
        ipaddress.ip_address(address)

    except ValueError:
        print(f"The IP address {address} is not valid")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-p', '--port', type=int, help='Port number to listen on')
    parser.add_argument('-f', '--file_name', type=str, help='File name to store the data in')
    parser.add_argument('-r', '--reliability', type=str, help='Choose reliability of the data transfer')
    parser.add_argument('-b', '--bind', type=str)

    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')

    args = parser.parse_args()

    check_ip(args.bind)
    if args.server:
        run_server(args.bind, args.port)

    elif args.client:
        run_client(args.bind, args.port)

