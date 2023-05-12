import time
from socket import *
import ipaddress
import argparse
import sys
from DRTP import *

def check_ip(ip_address):
    '''
    Checks if provided IP address is valid (-i flag)

    Args:
        ip_address(str): holds the provided IP address

    Returns:
        the IP address if it is valid, else an error is raised
    '''
    try:
        # convert argument to an IPv4 address
        ipaddress.ip_address(ip_address)
    except:
        # raise error if not a valid dotted decimal notation
        raise argparse.ArgumentTypeError("IP address must be in format e.g. 10.0.0.2")
    # return dotted decimal notation
    return ip_address


def check_port(port_number):
    '''
    Checks if provided port number is valid (-i flag)

    Args:
        ip_address(str): holds the provided IP address

    Returns:
        the port number if it is valid, else an error is raised
    '''
    try:
        # convert argument to an integer data type
        port_number = int(port_number)
    except ValueError:
        # raise error if not integer
        raise argparse.ArgumentTypeError("Port must be an integer")

    # raise error if not in range
    if not 1024 <= port_number <= 65535:
        raise argparse.ArgumentTypeError("Port must be in the range [1024, 65535]")
    # return int
    return port_number


def run_server(ip_address, port, reliable_method, window_size, test):
    '''
    Receives data using the specified reliability function and saves the received file to "received_file.jpg"

    Args:
        ip_address(str): the IP address to bind the socket to
        port(int): the port number to bind the socket to
        reliable_method(str): the reliability function to use, "SAW", "GBN", or "SR"
        window_size(int): the size of the sliding window, which is only used for "SR"
        test(boolean): whether or not to enable test mode, which is only used for "SAW" or "GBN"

    Returns:
        Void
    '''
    file_path = "received_file.jpg"
    received_data = b""

    try:
        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind((ip_address, port))

        print(f"Server listening on {ip_address}:{port}")

        if reliable_method == "SAW":
            received_data = RECV_SAW(server_socket, test)
        elif reliable_method == "GBN":
            received_data = RECV_GBN(server_socket, test)
        elif reliable_method == "SR":
            received_data = RECV_SR(server_socket, test, window_size)

        with open(file_path, "wb") as file:
            file.write(received_data)

        print(f"File received and saved to {file_path}")

    except KeyboardInterrupt:
        sys.exit()

    except Exception as e:
        print("Failed to bind. Error:", e)
        sys.exit()


def run_client(ip_address, port, reliable_method, file_path, window_size, test):
    '''
    Sends a file from to a server using different reliability protocols (SAW, GBN, SR)
    
    Args:
        ip_address(str): the IP address to bind the socket to
        port(int): the port number to bind the socket to
        reliable_method(str): the reliability function to use, "SAW", "GBN", or "SR"
        file_path(str): the full path of the file to transfer
        window_size(int): the size of the sliding window, which is only used for "SR" and "GBN"
        test(boolean): whether or not to enable test mode, which is only used for "SAW" and "GBN"

    Returns:
        Void, prints the calculated throughput of the data transmission
    '''
    try:
        sender_sock = socket(AF_INET, SOCK_DGRAM)
        addr = (ip_address, port)

        with open(file_path, "rb") as f:
            file_data = f.read()

    except IOError:
        print("Error opening file")
        sys.exit()

    try:
        start_time = time.monotonic()

        if reliable_method == "SAW":
            SEND_SAW(sender_sock, addr, file_data)
        elif reliable_method == "GBN":
            SEND_GBN(sender_sock, addr, file_data, window_size, test)
        elif reliable_method == "SR":
            SEND_SR(sender_sock, addr, file_data, window_size, test)

        elapsed_time = time.monotonic() - start_time
        throughput = (len(file_data) * 8 / elapsed_time) / (1024**2)
        print(f"\nBandwidth:{throughput:.2f}")

    except KeyboardInterrupt:
        sender_sock.close()
        sys.exit()

# Main function to run the tool
if __name__ == '__main__':
    # define the argument parser and provide a description
    parser = argparse.ArgumentParser(description="A custom reliable data transfer protocol", epilog="End of help")

    # add command line arguments to the parser
    parser.add_argument('-s', '--server', action='store_true', help='Run in server mode')
    parser.add_argument('-c', '--client', action='store_true', help='Run in client mode')
    parser.add_argument('-i', '--ip_address', type=check_ip, default='127.0.0.1', help='Choose IP address')
    parser.add_argument('-p', '--port', type=check_port, default=12000, help='Choose the port number')
    parser.add_argument('-f', '--file_name', type=str, default='./testFile.jpg', help='File name to store the data in')
    parser.add_argument('-r', '--reliability', type=str.upper, choices=['SAW', 'GBN', 'SR'], default='SAW', help='Choose reliability of the data transfer')
    parser.add_argument('-t', '--test', type=str.upper, default=False, help='Choose which artificial test case')
    parser.add_argument('-w', '--window', type=int, default=5, help='Select window size (only in GBN & SR)')

    # parse the command-line arguments
    args = parser.parse_args()

    # if the user has neither specified -s or -c flag, print error message and exit program 
    if not (args.server or args.client):
        print('Error: you must run either in server or client mode')
        sys.exit()
    # if the user has specified both -s or -c flag at the same time, print error message and exit program 
    if args.server and args.client:
        print('Error: you cannot run both server and client mode at once')
        sys.exit()

    # if the user specified -s flag, call run_server with the provided arguments
    if args.server:
        # if the user specified "SKIP_ACK" set 'True' for test
        if args.test == "SKIP_ACK":
            run_server(args.ip_address, args.port, args.reliability, args.window, True)
        # if test not specified set 'False' for test
        elif not args.test:
            run_server(args.ip_address, args.port, args.reliability, args.window, False)
        # If the user provided an invalid testing argument, print an error message and exit
        else:
            print("Type in 'skip_ack' as argument to test skipping ack msg")
            sys.exit()

    # if the user specified -c flag, call run_client with the provided arguments
    if args.client:
        # if the user specified "LOSS" set 'True' for test
        if args.test == "LOSS":
            run_client(args.ip_address, args.port, args.reliability, args.file_name, args.window, True)
        # if test not specified set 'False' for test
        elif not args.test:
            run_client(args.ip_address, args.port, args.reliability, args.file_name, args.window, False)
        # If the user provided an invalid testing argument, print an error message and exit
        else:
            print("Type in 'loss' as argument to test skipping sequence number")
            sys.exit()
