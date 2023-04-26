from socket import *
import ipaddress
import argparse
import sys
from header import *

# Define constants
BUFFER_SIZE = 1472
HEADER_SIZE = 12

# Define the simplified TCP header structure


def check_ip(address):
    try:
        ipaddress.ip_address(address)

    except ValueError:
        print(f"The IP address {address} is not valid")


def run_server(ip, port):
    file_path = 'received_file.png'             # Specify the file path for the received file
    try:
        # Create a socket using UDP
        server_socket = socket(AF_INET, SOCK_DGRAM)
        # Bind the socket to the given port
        server_socket.bind((ip, port))
        # Print a message to indicate that the server is listening on the specified IP address and port number
        print(f"Server listening on {ip}:{port}")

    except OSError as e:
        # Print an error message and exit the program if the socket cannot be bound to the specified IP address and port number
        print("Failed to bind. Error:", e)
        sys.exit()

    # Set the initial values for the three-way handshake
    handshake_complete = False
    expected_seq = 0
    window = 64

    try:
        # Begin the three-way handshake
        print("Establishing three-way handshake")
        while not handshake_complete:
            # Receive a SYN packet from the client
            syn_packet, addr = server_socket.recvfrom(BUFFER_SIZE)
            # Parse the header of the SYN packet
            syn_header = syn_packet[:12]
            seq, ack_nr, flags, win = parse_header(syn_header)
            syn, ack, fin = parse_flags(flags)

            # Check if the SYN packet has been received and the ACK flag is not set and the sequence number is as expected
            if syn and not ack and expected_seq == seq:
                print("Received SYN message from", addr)
                print(f"SYN_PACKET: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                print(f"SYN_FLAGS: syn={syn}, ack={ack}, fin={fin}")
                # Send a SYN-ACK packet to the client
                sequence_nr = 0
                ack_nr = seq
                flags = 12

                SYN_ACK = create_packet(sequence_nr, ack_nr, flags, window, b'')
                server_socket.sendto(SYN_ACK, addr)

                # Update the expected sequence number
                expected_seq += 1

            # Check if the ACK flag is set and the sequence number is as expected
            elif not syn and ack and expected_seq == seq:
                print("Received final ACK message from", addr)
                print(f"ACK_PACKET: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                print(f"ACK_FLAGS: syn={syn}, ack={ack}, fin={fin}")
                # Set the handshake as complete
                handshake_complete = True

    except OSError as e:
        # Print an error message and close the socket if an error occurs during the three-way handshake
        print("Error occurred during handshake:", e)
        server_socket.close()
        sys.exit()

    # Begin receiving the file data
    print("\n\nStarting to receive file data")

    last_acknowledged_seq = -1  # Initialize the last acknowledged sequence number to -1

    try:
        # Open the file for writing
        with open(file_path, 'wb') as file:
            while True:
                # Receive a packet from the client
                msg, addr = server_socket.recvfrom(BUFFER_SIZE)
                # Extract the header and data from the packet
                header_msg = msg[:12]
                data = msg[12:]

                # Parse the header
                seq, ack_nr, flags, win = parse_header(header_msg)
                syn, ack, fin = parse_flags(flags)

                # Check if the sequence number matches the expected sequence number
                if seq == expected_seq:
                    # Write the data to the file
                    file.write(data)

                    # Update the last acknowledged sequence number
                    last_acknowledged_seq = seq  # Update the last acknowledged sequence number

                    # Set the acknowledgement number to the received sequence number
                    ack_nr = seq

                    # Check if the packet contains the FIN flag
                    if fin:
                        # Set the flags to indicate the FIN and ACK flags are set
                        flags = 6
                        # Create the FIN/ACK packet and send it to the client
                        fin_ack_packet = create_packet(seq, ack_nr, flags, window, b'')
                        server_socket.sendto(fin_ack_packet, addr)
                        # End the loop
                        break

                    else:
                        # Set the flags to indicate that only the ACK flag is set
                        flags = 4
                        # Create the ACK packet and send it to the client
                        ack_packet = create_packet(seq, ack_nr, flags, window, b'')
                        server_socket.sendto(ack_packet, addr)
                        # Update the expected sequence number
                        expected_seq += 1

                # If the sequence number is less than the expected sequence number, ignore the packet
                elif seq < expected_seq:

                    # Received a duplicate packet, ignore it
                    pass

                # If the sequence number is greater than the expected sequence number, resend the last acknowledged ACK packet
                else:
                    # Received an out-of-order packet, resend the last acknowledged ACK packet
                    # Set the flags to indicate that only the ACK flag is set
                    flags = 4
                    # Create the ACK packet using the last acknowledged sequence number and send it to the client
                    ack_packet = create_packet(last_acknowledged_seq, ack_nr, flags, window, b'')
                    server_socket.sendto(ack_packet, addr)

    except OSError as e:
        # Handle errors that occurred during file transfer
        print("Error occurred during file transfer", e)
        sys.exit()



def run_client(server_ip, server_port):
    try:
        # Create a UDP socket
        client_sock = socket(AF_INET, SOCK_DGRAM)

    except OSError as e:
        print("Failed to create socket. Error:", e)
        sys.exit()

    # Specify the file path for the file
    file_path = '/Users/fahmimohammed/Screenshot 2023-04-24 at 22.58.35.png'
    print("Opening file")
    try:
        # Open the file to be transferred
        file = open(file_path, 'rb')
    except IOError as e:
        print("Failed to open file. Error:", e)
        sys.exit()

    # Initialize variables for the three-way handshake
    seq = 0
    data = b''
    ack_nr = 0
    win = 0
    flags = 8
    expected_ack = 0
    # Create a SYN packet and send it to the server
    syn_packet = create_packet(seq, ack_nr, flags, win, data)
    client_sock.sendto(syn_packet, (server_ip, server_port))

    # Wait for SYN-ACK packet from the server
    handshake_complete = False
    while not handshake_complete:
        try:
            # Receive SYN-ACK packet and parse its header and flags
            syn_ack_packet, addr = client_sock.recvfrom(1472)
            seq, ack_nr, flags, win = parse_header(syn_ack_packet[:12])
            syn, ack, fin = parse_flags(flags)

            # Check if the received packet is SYN-ACK and if the ACK number is as expected
            if ack and syn and ack_nr == expected_ack:
                print("Received SYN-ACK message from server", addr)
                print(f"SYN_ACK_PACKET: seq={seq}, ack_nr={ack_nr}, flags={flags}, win={win}")
                print(f"SYN_ACK_FLAGS: syn={syn}, ack={ack}, fin={fin}")

                # Update variables for ACK packet
                ack_nr = 0
                flags = 4
                seq += 1
                win = 0

                # Create and send the ACK packet
                ack_packet = create_packet(seq, ack_nr, flags, win, data)
                client_sock.sendto(ack_packet, addr)

                # Update the expected ACK number and indicate that the handshake is complete
                expected_ack += 1
                handshake_complete = True

        except timeout:
            # If the timeout occurs, resend the SYN packet
            print("Timeout: Resending SYN packet")
            client_sock.sendto(syn_packet, (server_ip, server_port))

    # The three-way handshake is complete
    print("Done with three-way handshake")

    # Start sending data packets to the server
    while True:
        # Read the file in chunks of 1460 bytes
        data = file.read(1460)

        # Initialize variables for the data packet
        ack_nr = 0
        win = 0
        flags = 0

        # If there is no more data to send, set flags to 2 (FIN)
        if not data:
            flags = 2
            data = b''
            # Create FIN packet and send to server
            fin_packet = create_packet(seq, ack_nr, flags, win, data)
            client_sock.sendto(fin_packet, (server_ip, server_port))
            # Break out of loop 
            break

        else:
            # Create packet and send to server
            packet = create_packet(seq, ack_nr, flags, win, data)
            client_sock.sendto(packet, (server_ip, server_port))

            # Wait for acknowledgement packet from server
            client_sock.settimeout(0.5)
            # Initialize an empty list to hold received ACKs
            received_acks = []
            while True:
                client_sock.settimeout(0.5)
                # Wait for an ACK packet to arrive
                try:
                    ack_packet, addr = client_sock.recvfrom(1472)
                    # Parse the header of the ACK packet 
                    seq, ack_nr, flags, win = parse_header(ack_packet)
                    # Parse the flags to determine if the packet is a SYN, ACK, or FIN packet
                    syn, ack, fin = parse_flags(flags)

                    # If ACK flag is set and acknowledgement number is expected, break out of loop
                    if ack and ack_nr == expected_ack:
                        print(f"Received ACK for packet", ack_nr)
                        expected_ack += 1
                        break

                    # If ACK number is less than expected, print message indicating duplicate ACK received
                    elif ack_nr < expected_ack:
                        print(f"Received a duplicate ACK for packet {ack_nr}")
                        # If ACK number has not already been received, add it to list of received ACKs and break out of loop
                        if ack_nr not in received_acks:
                            received_acks.append(ack_nr)
                            break

                except timeout:
                    # If timeout occurs, resend packet to server
                    client_sock.sendto(packet, (server_ip, server_port))

            # Increment sequence number for next packet
            seq += 1

    # Close client socket connection
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