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

    except OSError as e:
        print("Failed to bind. Error:", e)
        sys.exit()

    handshake_complete = False
    expected_seq = 0
    window = 64

    try:
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
                handshake_complete = True

    except OSError as e:
        print("Error occurred during handshake:", e)
        server_socket.close()
        sys.exit()

    print("\n\nStarting to receive file data")

    last_acknowledged_seq = -1  # Initialize the last acknowledged sequence number to -1

    try:
        with open(file_path, 'wb') as file:
            while True:
                msg, addr = server_socket.recvfrom(BUFFER_SIZE)
                header_msg = msg[:12]
                data = msg[12:]

                seq, ack_nr, flags, win = parse_header(header_msg)
                syn, ack, fin = parse_flags(flags)

                if seq == expected_seq:
                    file.write(data)

                    last_acknowledged_seq = seq  # Update the last acknowledged sequence number

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


                elif seq < expected_seq:

                    # Received a duplicate packet, ignore it

                    pass

                else:

                    # Received an out-of-order packet, resend the last acknowledged ACK packet

                    flags = 4

                    ack_packet = create_packet(last_acknowledged_seq, ack_nr, flags, window, b'')

                    server_socket.sendto(ack_packet, addr)


    except OSError as e:
        print("Error occurred during file transfer", e)
        sys.exit()



def run_client(server_ip, server_port):
    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 22.58.35.png'

    try:
        client_sock = socket(AF_INET, SOCK_DGRAM)

    except OSError as e:
        print("Failed to create socket. Error:", e)
        sys.exit()

    addr = (server_ip, server_port)
    while True:
       send_data(client_sock, )



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