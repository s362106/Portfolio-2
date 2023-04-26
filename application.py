from socket import *
import ipaddress
import argparse
import sys
from header import *


BUFFER_SIZE = 1472
HEADER_SIZE = 12

# Define the simplified TCP header structure

drtp = DRTP()

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

    handshake_complete = drtp.handle_handshake(server_socket)
    if handshake_complete:
        print("Handshake success")
        packet, addr = server_socket.recvfrom(1472)
        data = drtp.receive_data(server_socket, packet, addr[0], addr[1])
        print(data)

    else:
        print("Handshake failed.")
        sys.exit()

def run_client(server_ip, server_port):
    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 22.58.35.png'

    try:
        sender_socket = socket(AF_INET, SOCK_DGRAM)


        handshake_complete = drtp.start_handshake(sender_socket, server_ip, server_port)
        if handshake_complete:
            #send_packet(sender_socket, (server_ip, server_port), file_path)
            print("Handshake complete")
            data = b'Hei'
            drtp.send_data(sender_socket, server_ip, server_port, data)

        else:
            print("Handshake not complete")
            sys.exit()

    except:
        sys.exit()





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