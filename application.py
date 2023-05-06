import time
from socket import *
import ipaddress
import argparse
import sys
from DRTP import *


# Define the simplified TCP header structure

def check_ip(ip_address):
    try:
        # convert argument to an IPv4 address 
        ipaddress.ip_address(ip_address)
    except:
        # raise error if not a valid dotted decimal notation
        raise argparse.ArgumentTypeError('IP address must be in format e.g. 10.0.0.2')
    # return dotted decimal notation 
    return ip_address


def check_port(port_number):
    try:
        # convert argument to an integer data type
        port_number = int(port_number)
    except ValueError:
        # raise error if not integer                       
        raise argparse.ArgumentTypeError('Port must be an integer')

    # raise error if not in range
    if not 1024 <= port_number <= 65535:
        raise argparse.ArgumentTypeError('Port must be in the range [1024, 65535]')
    # return int
    return port_number


def run_server(ip, port, reliability_func, window_size, test):
    file_path = 'received_file.png'
    received_data = b''
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))

        print(f"Server listening on {ip}:{port}")

    except Exception as e:
        print("Failed to bind. Error:", e)
        sys.exit()

    try:
        if reliability_func == "SAW":
            received_data = RECV_STOP(server_socket, test)
        elif reliability_func == "GBN":
            received_data = RECV_GBN(server_socket, test)
        elif reliability_func == "SR":
            received_data = RECV_SR(server_socket, test, window_size)
        else:
            print("Invalid reliability function specified")
            sys.exit()

    except KeyboardInterrupt:
        server_socket.close()
        sys.exit()

    try:
        with open(file_path, 'wb') as file:
            file.write(received_data)

    except IOError:
        print("Error opening file")
        sys.exit()

    print(f"File received and saved to {file_path}")


def run_client(ip, port, reliability_func, file_path, window_size, test):
    try:
        sender_sock = socket(AF_INET, SOCK_DGRAM)
        addr = (ip, port)
        with open(file_path, 'rb') as f:
            file_data = f.read()

    except IOError:
        print("Error opening file")
        sys.exit()

    try:
        start_time = time.monotonic()
        if reliability_func == "SAW":
            SEND_SAW(sender_sock, addr, file_data)
        elif reliability_func == "GBN":
            SEND_GBN(sender_sock, addr, file_data, window_size, test)
        elif reliability_func == "SR":
            SEND_SR(sender_sock, addr, file_data, window_size, test)
        else:
            print("Invalid reliability function specified")

        elapsed_time = time.monotonic() - start_time
        bandwidth = (len(file_data) * 8 / elapsed_time) / (1024**2)
        print(f"\nBandwidth:{bandwidth:.2f}")
    except KeyboardInterrupt:
        sender_sock.close()
        sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')
    parser.add_argument('-i', '--ip_address', type=check_ip, default='127.0.0.1', help='Choose IP address')
    parser.add_argument('-p', '--port', type=check_port, default=12000, help='Choose the port number')
    parser.add_argument('-f', '--file_name', type=str, default='./Screenshot 2023-04-28 at 19.57.31.png', help='File name to store the data in')
    parser.add_argument('-r', '--reliability', type=str.upper, choices=['SAW', 'GBN', 'SR'], default='SAW', help='Choose reliability of the data transfer')
    parser.add_argument('-t', '--test', type=str.upper, default=False, help='Choose which artificial test case')
    parser.add_argument('-w', '--window', type=int, default=5, help='Select window size (only in GBN & SR)')

    args = parser.parse_args()

    if args.server:

        if args.test == 'SKIP_ACK':
            run_server(args.ip_address, args.port, args.reliability, args.window, True)

        elif not args.test:
            run_server(args.ip_address, args.port, args.reliability, args.window, False)

        else:
            print("Type in skip_ack as argument to test skipping ack msg")
            sys.exit()

    elif args.client:
        if args.test == 'LOSS':
            run_client(args.ip_address, args.port, args.reliability, args.file_name, args.window, True)

        elif not args.test:
            run_client(args.ip_address, args.port, args.reliability, args.file_name, args.window, False)
        else:
            print("Type in 'loss' as argument to test skipping sequence number")
            sys.exit()
