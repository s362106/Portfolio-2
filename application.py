from socket import *
import ipaddress
import argparse
import sys
from header import *

BUFFER_SIZE = 1472
HEADER_SIZE = 12

# Define the simplified TCP header structure


def check_ip(address):
    try:
        ipaddress.ip_address(address)

    except ValueError:
        print(f"The IP address {address} is not valid")


def run_server(ip, port):
    file_path = 'received_file.png'
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))

        print(f"Server listening on {ip}:{port}")

    except Exception as e:
        print("Failed to bind. Error:", e)
        sys.exit()

    handshake_complete = False
    while not handshake_complete:
        syn_packet, addr = server_socket.recvfrom(BUFFER_SIZE)
        syn_header = syn_packet[:12]
        seq, ack_nr, flags, win = parse_header(syn_header)
        syn, ack, fin = parse_flags(flags)

        if syn and not ack:
            print("Received SYN message from", addr)
            sequence_nr = 0
            ack_nr = seq
            flags = 12

            SYN_ACK = create_packet(sequence_nr, ack_nr, flags, 0, b'')

            server_socket.sendto(SYN_ACK, addr)

        elif not syn and ack:
            print("Received final ACK message from", addr)
            handshake_complete = True

    with open(file_path, 'wb') as file:



def run_client(server_ip, server_prt):
    try:
        client_sock = socket(AF_INET, SOCK_DGRAM)

    except Exception as e:
        print("Failed to send data. Error:", e)
        sys.exit()

    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 22.58.35.png'


    file = open(file_path, 'rb')

    seq = 0
    data = b''
    ack_nr = 0
    win = 64
    flags = 8
    expected_ack = 0
    syn_packet = create_packet(seq, ack_nr, flags, win, data)
    client_sock.sendto(syn_packet, (server_ip, server_prt))

    handshake_complete = False
    while not handshake_complete:

        client_sock.settimeout(0.5)
        try:
            syn_ack_packet, addr = client_sock.recvfrom(1472)
            seq, ack_nr, flags, win = parse_header(syn_ack_packet[:12])
            syn, ack, fin = parse_flags(flags)

            if ack and syn and ack_nr == expected_ack:
                print("Received SYN-ACK message from server", addr)
                ack_nr = seq + 1
                flags = 4
                seq += 1

                ack_packet = create_packet(seq, ack_nr, flags, win, data)
                client_sock.sendto(ack_packet, addr)
                expected_ack += 1

                handshake_complete = True

        except timeout:
            print("Timeout: Resending SYN packet")
            client_sock.sendto(syn_packet, (server_ip, server_prt))

    client_sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-p', '--port', type=int, default=12000, help='Choose the port number')
    parser.add_argument('-f', '--file_name', type=str, help='File name to store the data in')
    parser.add_argument('-r', '--reliability', type=str, help='Choose reliability of the data transfer')
    parser.add_argument('-b', '--bind', type=str, default='127.0.0.1', help='Choose IP address')

    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')

    args = parser.parse_args()

    if args.server:
        check_ip(args.bind)
        run_server(args.bind, args.port)

    elif args.client:
        check_ip(args.bind)
        run_client(args.bind, args.port)