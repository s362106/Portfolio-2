import time
from socket import *
import ipaddress
import argparse
import sys
from DRTP import *

# Her er det en endring

BUFFER_SIZE = 1472
HEADER_SIZE = 12


# Define the simplified TCP header structure

def check_ip(address):
    try:
        ipaddress.ip_address(address)

    except ValueError:
        print(f"The IP address {address} is not valid")

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
        

def run_server(ip, port, reliability_func):
    file_path = 'received_file.png'
    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip, port))

        print(f"Server listening on {ip}:{port}")

    except Exception as e:
        print("Failed to bind. Error:", e)
        sys.exit()

    print("Performing three-way handshake")

    if reliability_func == "SAW":
        received_data = RECV_STOP(server_socket, False)
    
    elif reliability_func == "GBN":
        received_data = RECV_GBN(server_socket)

    #elif reliability_func == "SR":
        #received_data = RECV_SR(server_socket)

    else:
        print("Invalid reliability function specified")
    
    try:
        with open(file_path, 'wb') as file:
            file.write(received_data)

    except IOError:
        print("Error opening file")
        sys.exit()

    print(f"File received and saved to {file_path}")
    server_socket.close()


def run_client(ip, port, reliability_func, file_path):
    try:
        sender_sock = socket(AF_INET, SOCK_DGRAM)
        addr = (ip, port)
        with open(file_path, 'rb') as f:
            file_data = f.read()

    except IOError:
        print("Error opening file")
        sys.exit()

    if reliability_func == "SAW":
        stop_and_wait(sender_sock, addr, file_data)
    
    elif reliability_func == "GBN":
        GBN(sender_sock, addr, file_data, window_size=15)
    
    else:
        print("Invalid reliability function specified")


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
                if reliable_mode == "SAW":
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
    



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')
    parser.add_argument('-i', '--ip_address', type=check_ip, default='127.0.0.1', help='Choose IP address')
    parser.add_argument('-p', '--port', type=check_port, default=12000, help='Choose the port number')
    parser.add_argument('-f', '--file_name', type=str, default='./Screenshot 2023-04-28 at 19.57.31.png', help='File name to store the data in')
    parser.add_argument('-r', '--reliability', choices=['SAW', 'GBN', 'SR'], default='SAW', help='Choose reliability of the data transfer')
    parser.add_argument('-t', '--test', type=str, default='', help='Choose which artificial test case')
    parser.add_argument('-w', '--window', type=int, default=5, help='Select window size (only in GBN & SR)')

    args = parser.parse_args()

    if args.server:
        run_server(args.ip_address, args.port, str(args.reliability).upper())

    elif args.client:
        run_client(args.ip_address, args.port, str(args.reliability).upper(), args.file_name)

