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
        drtp = DRTP(server_socket, ip, port, 'Ingenting')

        with open(file_path, 'wb') as file:
            while True:
                data = drtp.receive()
                if not data:
                    break
                file.write(data)
        '''while True:
            data = drtp.receive()
            print(data)'''

    except OSError as e:
        print("Failed to bind. Error:", e)
        sys.exit()



def run_client(server_ip, server_port):
    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 22.58.35.png'

    try:
        sender_sock = socket(AF_INET,SOCK_DGRAM)

        drtp = DRTP(sender_sock, server_ip, server_port, 'Ingenting')
        #send_packet(sender_socket, (server_ip, server_port), file_path)
        print("Handshake complete")
        with open(file_path, 'rb') as file:
            data = file.read(1460)
            while data:

                drtp.send_and_wait(data)
                data = file.read(1460)

        '''for i in range(15):
            data = f"Her data nr. {i}"
            drtp.send_and_wait(data.encode())'''


    except IOError:
        print("Error opening file")
        sys.exit()





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-p', '--port', type=int, default=12000, help='Choose the port number')
    parser.add_argument('-f', '--file_name', type=str, help='File name to store the data in')
    parser.add_argument('-r', '--reliability', type=str, help='Choose reliability of the data transfer')
    parser.add_argument('-i', '--ip_address', type=str, default='127.0.0.1', help='Choose IP address')

    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')

    args = parser.parse_args()

    if args.server:
        check_ip(args.ip_address)
        run_server(args.ip_address, args.port)

    elif args.client:
        check_ip(args.ip_address)
        run_client(args.ip_address, args.port)