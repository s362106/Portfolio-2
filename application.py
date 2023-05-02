import time
from socket import *
import ipaddress
import argparse
import sys
from DRTP import *

BUFFER_SIZE = 1472
HEADER_SIZE = 12


# Define the simplified TCP header structure

def check_ip(address):
    try:
        ipaddress.ip_address(address)

    except ValueError:
        print(f"The IP address {address} is not valid")


def run_server_saw(ip, port, reliable_mode, test):
    file_path = 'received_file.png'
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))
        print(f"Server listening on {ip}:{port}")

        received_data = RECV_STOP(server_socket, False)
        with open(file_path, 'wb') as file:
            file.write(received_data)

    except OSError as e:
        print("Failed to bind. Error:", e)
        sys.exit()


def run_server_gbn(server_ip, server_port):
    file_path = 'received_file.png'
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((server_ip, server_port))
        print(f"Server listening on {server_ip}:{server_port}")

        received_data = RECV_GBN(server_socket)

        with open(file_path, 'wb') as file:
            file.write(received_data)

    except OSError as e:
        print("Failed to bind. Error:", e)
        sys.exit()


def test_skip_ack(ip, port, reliable_mode):
    file_path = 'received_file.png'
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))
        print(f"Server listening on {ip}:{port}")
        # drtp = DRTP(server_socket, ip, port, reliable_mode)
        first = 1
        with open(file_path, 'wb') as file:
            start_time = time.time()

            while True:
                if reliable_mode == "stop_and_wait":
                    if first == 1:
                        data = RECV_STOP(server_socket, test=True)
                        first += 1
                    else:
                        data = RECV_STOP(server_socket, test)
                    if not data:
                        break
                    file.write(data)
                    test = False

                else:
                    print("Reliable method chosen is not yet working")
                    sys.exit()
            elapsed_time = time.time() - start_time
            print("Tranfser time:", elapsed_time)
    except OSError as e:
        print("Failed to bind. Error:", e)
        sys.exit()


def run_client_gbn(recv_ip, recv_port, window):
    file_path = './Screenshot 2023-04-28 at 19.57.31.png'
    try:
        sender_sock = socket(AF_INET, SOCK_DGRAM)
        addr = (recv_ip, recv_port)
        with open(file_path, 'rb') as f:
            file_data = f.read()

        GBN(sender_sock, addr, file_data, window_size=15)
        #GBN(sender_sock, addr, file_path, window)

    except IOError:
        print("Error opening file")
        sys.exit()


def run_client_saw(server_ip, server_port):
    file_path = './Screenshot 2023-04-28 at 19.57.31.png'

    try:
        sender_sock = socket(AF_INET, SOCK_DGRAM)

        print("Handshake complete")
        addr = (server_ip, server_port)
        with open(file_path, 'rb') as file:
            file_data = file.read()

        stop_and_wait(sender_sock, addr, file_data)

    except IOError:
        print("Error opening file")
        sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-p', '--port', type=int, default=12000, help='Choose the port number')
    parser.add_argument('-f', '--file_name', type=str, default='Screenshot 2023-04-28 at 19.57.31.png', help='File name to store the data in')
    parser.add_argument('-r', '--reliability', type=str, default='saw',
                        help='Choose reliability of the data transfer')
    parser.add_argument('-i', '--ip_address', type=str, default='127.0.0.1', help='Choose IP address')
    parser.add_argument('-t', '--test', type=str, default='', help='Choose which artificial test case')
    parser.add_argument('-w', '--window', type=int, default=5, help='Select window size (only in GBN & SR)')
    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')

    args = parser.parse_args()

    if args.server:

        if str(args.reliability).upper() == 'gbn'.upper():
            run_server_gbn(args.ip_address, args.port)

        elif str(args.reliability).upper() == 'saw'.upper():
            run_server_saw(args.ip_address, args.port, args.reliability, args.test)

    elif args.client:
        if str(args.reliability).upper() == 'gbn'.upper():
            run_client_gbn(args.ip_address, args.port, args.window)

        elif str(args.reliability).upper() == 'saw'.upper():
            run_client_saw(args.ip_address, args.port)
