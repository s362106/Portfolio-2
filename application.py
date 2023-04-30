import time
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


def run_server(ip, port, reliable_mode, test):
    file_path = 'received_file.png'
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))
        print(f"Server listening on {ip}:{port}")
        #drtp = DRTP(server_socket, ip, port, reliable_mode)

        with open(file_path, 'wb') as file:
            start_time = time.time()
            while True:
                if reliable_mode == "stop_and_wait":
                    data = receive(server_socket, test)
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
                        data = receive(server_socket, test=True)
                        first += 1
                    else:
                        data = receive(server_socket, test)
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



def run_client(server_ip, server_port, reliable_mode, test):
    file_path = './Screenshot 2023-04-28 at 19.57.31.png'

    try:
        sender_sock = socket(AF_INET,SOCK_DGRAM)

        #drtp = DRTP(sender_sock, server_ip, server_port, reliable_mode)
        #send_packet(sender_socket, (server_ip, server_port), file_path)
        print("Handshake complete")
        with open(file_path, 'rb') as file:
            data = file.read(1460)
            while data:
                addr = (server_ip, server_port)
                stop_and_wait(sender_sock, addr, data)
                data = file.read(1460)
                if not data:
                    close_conn(sender_sock, addr)


    except IOError:
        print("Error opening file")
        sys.exit()


def skip_seq_num(server_ip, server_port, reliable_method):
    file_path = './Screenshot 2023-04-28 at 19.57.31.png'

    try:
        sender_sock = socket(AF_INET, SOCK_DGRAM)

        # drtp = DRTP(sender_sock, server_ip, server_port, reliable_mode)
        # send_packet(sender_socket, (server_ip, server_port), file_path)
        print("Handshake complete")
        with open(file_path, 'rb') as file:
            data = file.read(1460)
            while data:
                addr = (server_ip, server_port)
                stop_and_wait(sender_sock, addr, data, test=True)
                data = file.read(1460)
                if not data:
                    close_conn(sender_sock, addr)


    except IOError:
        print("Error opening file")
        sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-p', '--port', type=int, default=12000, help='Choose the port number')
    parser.add_argument('-f', '--file_name', type=str, help='File name to store the data in')
    parser.add_argument('-r', '--reliability', type=str, default='stop_and_wait', help='Choose reliability of the data transfer')
    parser.add_argument('-i', '--ip_address', type=str, default='127.0.0.1', help='Choose IP address')
    parser.add_argument('-t', '--test', type=str, default='', help='Choose which artificial test case')

    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')

    args = parser.parse_args()

    if args.server:
        if args.test == 'skip':
            check_ip(args.ip_address)
            test_skip_ack(args.ip_address, args.port, args.reliability)

        elif args.test == '':
            run_server(args.ip_address, args.port, args.reliability, args.test)

    elif args.client:
        if args.test == 'skip_seq':
            skip_seq_num(args.ip_address, args.port, args.reliability)
        else:
            check_ip(args.ip_address)
            run_client(args.ip_address, args.port, args.reliability, args.test)