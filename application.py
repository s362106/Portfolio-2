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

    print("Performing three-way handshake")

    handshake_complete = False
    while not handshake_complete:
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
            handshake_complete = True

    expected_seq = 1
    with open(file_path, 'wb') as file:
        while True:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
            header_msg = data[:12]
            msg = data[12:]

            seq, ack_nr, flags, win = parse_header(header_msg)

            syn, ack, fin = parse_flags(flags)
            print(f"Header values seq={seq}, ack={ack}, and fin={fin}")

            if seq == expected_seq:
                file.write(msg)

                if fin:
                    ack_nr = seq + 1
                    flags = 6
                    fin_ack_packet = create_packet(seq, ack_nr, flags, 0, b'')

                    server_socket.sendto(fin_ack_packet, addr)
                    break

                else:
                    ack_nr = seq +1
                    flags = 4
                    ack_packet = create_packet(seq, ack_nr, flags, 0, b'')

                    server_socket.sendto(ack_packet, addr)

                expected_seq += 1
            else:
                ack_nr = expected_seq
                flags = 4
                ack_packet = create_packet(seq, ack_nr, flags, win, b'')
                server_socket.sendto(ack_packet, addr)
                print(f"Resent ACK for packet {ack_nr}")


def run_client(server_ip, server_prt):
    try:
        client_sock = socket(AF_INET, SOCK_DGRAM)

    except Exception as e:
        print("Failed to send data. Error:", e)
        sys.exit()

    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 22.58.35.png'

    print("Åpner filen")
    file = open(file_path, 'rb')

    seq_nr = 0
    data = b''
    ack_nr = 0
    win = 64
    flags = 8
    syn_packet = create_packet(seq_nr, ack_nr, flags, win, data)
    client_sock.sendto(syn_packet, (server_ip, server_prt))

    handshake_complete = False
    while not handshake_complete:

        client_sock.settimeout(0.5)
        try:
            syn_ack_packet, addr = client_sock.recvfrom(BUFFER_SIZE)
            seq, ack_nr, flags, win = parse_header(syn_ack_packet[:12])
            syn, ack, fin = parse_flags(flags)

            if ack and syn and ack_nr == seq_nr + 1:
                print("Received SYN-ACK message")
                ack_nr = seq_nr + 1
                flags = 4
                seq_nr += 1

                ack_packet = create_packet(seq_nr, ack_nr, flags, win, data)
                client_sock.sendto(ack_packet, addr)
                print("Sent ACK message")
                handshake_complete = True

        except timeout:
            print("Timeout: Resending SYN packet")
            client_sock.sendto(syn_packet, (server_ip, server_prt))

    while True:
        data = file.read(1460)

        if not data:
            print("Sender FIN message")
            flags = 2
            data = b''
            packet = create_packet(seq_nr, 0, flags, 64, data)

            client_sock.sendto(packet, (server_ip, server_prt))
            break

        else:
            packet = create_packet(seq=seq_nr, ack=0, flags=0, win=0, data=data)
            client_sock.sendto(packet, (server_ip, server_prt))
            seq_nr += 1

            client_sock.settimeout(2)

            while True:
                try:
                    ack_packet, addr = client_sock.recvfrom(BUFFER_SIZE)
                    seq, ack_nr, flags, win = parse_header(ack_packet)
                    syn, ack, fin = parse_flags(flags)

                    if ack and ack_nr == seq_nr:
                        print(f"Received ACK for packet {seq_nr}")
                        break

                except timeout:
                    print(f"Timeout: Resending packet {seq_nr}")
                    client_sock.sendto(packet, (server_ip, server_prt))

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