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
    expected_seq = 0
    window = 64

    print("Establishing three-way handshake")
    while not handshake_complete:
        syn_packet, addr = server_socket.recvfrom(BUFFER_SIZE)
        syn_header = syn_packet[:12]
        seq, ack_nr, flags, win = parse_header(syn_header)
        syn, ack, fin = parse_flags(flags)

        if syn and not ack and expected_seq == seq:
            print("Received SYN message from", addr)
            print(f"SYN_PACKET: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
            print(f"SYN_FLAGS: syn={syn}, ack={ack}, fin={fin}")
            sequence_nr = 0
            ack_nr = seq
            flags = 12

            SYN_ACK = create_packet(sequence_nr, ack_nr, flags, window, b'')

            server_socket.sendto(SYN_ACK, addr)
            expected_seq += 1

        elif not syn and ack and expected_seq == seq:
            print("Received final ACK message from", addr)
            print(f"ACK_PACKET: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
            print(f"ACK_FLAGS: syn={syn}, ack={ack}, fin={fin}")
            expected_seq += 1
            handshake_complete = True

    print("\n\nStarting to receive file data")
    with open(file_path, 'wb') as file:
        while True:
            msg, addr = server_socket.recvfrom(BUFFER_SIZE)
            header_msg = msg[:12]
            data = msg[12:]

            seq, ack_nr, flags, win = parse_header(header_msg)
            syn, ack, fin = parse_flags(flags)

            if seq == expected_seq:
                file.write(data)

                ack_nr = seq
                if fin:
                    flags = 6
                    fin_ack_packet = create_packet(seq, ack_nr, flags, window, b'')

                    server_socket.sendto(fin_ack_packet, addr)
                    break

                else:
                    flags = 4
                    ack_packet = create_packet(seq, ack_nr, flags, window, b'')
                    server_socket.sendto(ack_packet, addr)
                    expected_seq += 1

            else:
                ack_nr = seq
                flags = 4
                ack_packet = create_packet(seq, ack_nr, flags, 64, b'')
                server_socket.sendto(ack_packet, addr)
                print(f"Resent ACK for packet {ack_nr}")



def run_client(server_ip, server_port):
    try:
        client_sock = socket(AF_INET, SOCK_DGRAM)

    except Exception as e:
        print("Failed to send data. Error:", e)
        sys.exit()

    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 22.58.35.png'

    print("Opening file")
    file = open(file_path, 'rb')

    seq = 0
    data = b''
    ack_nr = 0
    win = 0
    flags = 8
    expected_ack = 0
    syn_packet = create_packet(seq, ack_nr, flags, win, data)
    client_sock.sendto(syn_packet, (server_ip, server_port))

    handshake_complete = False
    while not handshake_complete:

        client_sock.settimeout(0.5)
        try:
            syn_ack_packet, addr = client_sock.recvfrom(1472)
            seq, ack_nr, flags, win = parse_header(syn_ack_packet[:12])
            syn, ack, fin = parse_flags(flags)

            if ack and syn and ack_nr == expected_ack:
                print("Received SYN-ACK message from server", addr)
                print(f"SYN_ACK_PACKET: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                print(f"SYN_ACK_FLAGS: syn={syn}, ack={ack}, fin={fin}")
                ack_nr = 0
                flags = 4
                seq += 1
                win = 0

                ack_packet = create_packet(seq, ack_nr, flags, win, data)
                client_sock.sendto(ack_packet, addr)
                expected_ack += 1

                handshake_complete = True

        except timeout:
            print("Timeout: Resending SYN packet")
            client_sock.sendto(syn_packet, (server_ip, server_port))

    print("Done with three-way handshake")
    while True:
        data = file.read(1460)

        ack_nr = 0
        win = 0
        flags = 0

        if not data:
            flags = 2
            data = b''
            fin_packet = create_packet(seq, ack_nr, flags, win, data)

            client_sock.sendto(fin_packet, (server_ip, server_port))
            break

        else:
            packet = create_packet(seq, ack_nr, flags, win, data)
            client_sock.sendto(packet, (server_ip, server_port))


            client_sock.settimeout(3)

            while True:
                try:
                    ack_packet, addr = client_sock.recvfrom(1472)
                    seq, ack_nr, flags, win = parse_header(ack_packet)
                    syn, ack, fin = parse_flags(flags)

                    if ack and ack_nr == expected_ack:
                        print(f"Received ACK for packet", ack_nr)
                        break

                except timeout:
                    client_sock.sendto(packet, (server_ip, server_port))

            expected_ack += 1
            seq += 1


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