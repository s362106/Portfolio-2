import time
from struct import *
from socket import *
import sys

TIMEOUT = 0.5

# Header format
header_format = '!IIHH'

handshake_complete = False
sent_seq_num = 1
expected_seq_num = 1

next_seq_num = 1
base_seq_num = 1


def create_packet(seq_num, ack_num, flags, window_size, data):
    header = pack(header_format, seq_num, ack_num, flags, window_size)
    packet = header + data
    return packet


def parse_header(header):
    header_from_msg = unpack(header_format, header)
    return header_from_msg


def parse_flags(flags):
    syn = (flags >> 3) & 1
    ack = (flags >> 2) & 1
    fin = (flags >> 1) & 1

    return syn, ack, fin


def send(sock, data, seq_num, addr):
    packet = create_packet(seq_num, 0, 0, 0, data)
    #print("Sent packet with seq_num", seq_num)

    sock.sendto(packet, addr)
    #return seq_num


def send_ack(sock, ack_num, addr):
    ack_msg = create_packet(0, ack_num, 4, 64, b'')
    sock.sendto(ack_msg, addr)


def initiate_handshake(sock, addr):
    global handshake_complete

    # If handshake has not yet been completed, establish connection
    if not handshake_complete:
        flags = 8   # 1 0 0 0 = SYN flag value
        syn_packet = create_packet(0, 0, flags, 0, b'')     # Create SYN packet
        sock.sendto(syn_packet, addr)   # Send SYN packet to destination address
        print("Sent SYN packet with seq_num", 0)

        while True:
            # Set a timeout of 0.5 seconds for the socket for receiving SYN-ACK message
            sock.settimeout(0.5)
            try:
                synack_msg, addr = sock.recvfrom(1472)  # Receive message from the destination address
                header_from_msg = synack_msg[:12]  # Extract the header from the received message
                seq_num, ack_num, flags, win = parse_header(header_from_msg)  # Parse the header fields
                syn, ack, fin = parse_flags(flags)  # Parse the flags

                # If received SYN-ACK message is valid, send final ACK packet and complete handshake
                if syn and ack and not fin:
                    print("Received SYN-ACK msg with ak_num", ack_num)
                    flags = 4  # 0 1 0 0 = ACK flag value
                    ack_packet = create_packet(0, 0, flags, 0, b'')  # Create final ACK packet
                    sock.sendto(ack_packet, addr)  # Send ACK to destination address
                    print("Sent final ACK packet with ack_num", 0)
                    handshake_complete = True  # Set handshake_complete  to True
                    break

            # If timeout occurs, resend SYN packet
            except timeout:
                print(f"Timeout occurred. Resending SYN packet with seq_num 0")
                flags = 8  # 1 0 0 0 = SYN flag value
                syn_packet = create_packet(0, 0, flags, 0, b'')  # Create new SYN packet
                sock.sendto(syn_packet, addr)  # Send new SYN packet to destination address


def handle_handshake(sock):
    global handshake_complete
    if not handshake_complete:

        while True:
            try:
                syn_packet, addr = sock.recvfrom(1472)
                header = syn_packet[:12]
                syn, ack, fin = parse_flags(parse_header(header)[2])

                if syn and not ack and not fin:
                    print("Received SYN msg")
                    syn_ack_msg = create_packet(0, 0, 12, 64, b'')
                    sock.sendto(syn_ack_msg, addr)

                elif not syn and ack and not fin:
                    print("Received final ACK msg")
                    handshake_complete = True
                    break

            except Exception as e:
                print("Error:", e)
                sys.exit()


def stop_and_wait(sock, addr, filename):
    """
    Implements the Stop_and_Wait protocol for reliable data transfer over UDP

    Arguments:
        sock (socket): The UDP socket object
        addr (Tuple): A tuple containing the IP address and port number of the remote host
        data (bytes): The data to be sent

    Returns:
        None
    """

    # Declare global variables that will be modified within this function
    global sent_seq_num

    # If handshake has not yet been completed, establish connection
    initiate_handshake(sock, addr)

    # Once handshake is complete, send data packets and wait for ACKs

    with open(filename, 'rb') as file:

        while True:
            data = file.read(1460)
            if not data:
                close_conn(sock, addr)
                break

            send(sock, data, sent_seq_num, addr)  # Send first data packet with current sequence number

            # Wait for ACK message from the receiver
            received_ack = False
            while not received_ack:
                # Set a timeout og 0.5 seconds for the socket for receiving ACK message

                try:
                    ack_msg, addr = sock.recvfrom(1472)     # Receive message from destination address
                    header_from_msg = ack_msg[:12]  # Extract the header from the received message
                    seq_num, ack_num, flags, win = parse_header(header_from_msg)    # Parse the header fields
                    syn, ack, fin = parse_flags(flags)  # Parse the flags

                    # If received ACK message is valid, update global sequence number and set received_ack to True
                    if ack and ack_num == sent_seq_num:
                        print(f"ACK msg: ack_num={ack_num}, flags={flags}")
                        sent_seq_num += 1
                        received_ack = True
                        sent = True

                    # Else if received duplicate ACK message
                    elif ack and ack_num == sent_seq_num - 1:
                        print("Received duplicate ACK msg with ack_num", ack_num)
                        send(sock, data, sent_seq_num - 1, addr)

                    else:
                        sock.settimeout(0.5)

                except timeout:
                    print(f"Timeout occurred. Resending packet with seq_num={sent_seq_num}, flags=0")
                    send(sock, data, sent_seq_num, addr)


def receive(sock, test, filename):
    global handshake_complete
    if not handshake_complete:
        received_final_ack = False
        while not received_final_ack:

            try:
                syn_packet, addr = sock.recvfrom(1472)
                header = syn_packet[:12]
                syn, ack, fin = parse_flags(parse_header(header)[2])

                if syn and not ack and not fin:
                    print("Received SYN msg")
                    syn_ack_msg = create_packet(0, 0, 12, 64, b'')
                    sock.sendto(syn_ack_msg, addr)

                elif not syn and ack and not fin:
                    print("Received final ACK msg")
                    handshake_complete = True
                    received_final_ack = True

            except Exception as e:
                print("Error:", e)
                sys.exit()

    global expected_seq_num
    with open(filename, 'wb') as f:
        while True:
            msg, addr = sock.recvfrom(1472)

            header_from_msg = msg[:12]
            seq_num, ack_num, flags, win = parse_header(header_from_msg)
            syn, ack, fin = parse_flags(flags)

            if test:
                time.sleep(1)

            if not fin and not syn and not ack and seq_num == expected_seq_num:
                print(f"Received packet with seq_num", seq_num)
                app_data = msg[12:]
                send_ack(sock, expected_seq_num, addr)
                expected_seq_num += 1
                #ack_msg = create_packet(0, global_ack_num, flags, win, b'')

                #sock.sendto(ack_msg, addr)
                print("Sent ACK msg with ack_num", expected_seq_num - 1)

                f.write(app_data)

            # Usikker om man skal resende ACK melding til forrige packet hvis man får det igjen
            elif not fin and not syn and not ack and seq_num != expected_seq_num:
                print(f"Received duplicate packet with seq_num", seq_num)

                send_ack(sock, expected_seq_num - 1, addr)
                #ack_msg = create_packet(0, global_ack_num - 1, flags, win, b'')

                #sock.sendto(ack_msg, addr)

            if fin and not ack and not syn and seq_num == expected_seq_num:
                print("FIN msg received with seq_num", seq_num)
                flags = 4
                send_ack(sock, expected_seq_num, addr)
                #fin_ack_msg = create_packet(0, global_ack_num, flags, win, b'')
                #sock.sendto(fin_ack_msg, addr)

                acknowledgment_num = seq_num + 1
                sock.close()
                return


def close_conn(sock, addr):
    global sent_seq_num

    flags = 2
    fin_msg = create_packet(sent_seq_num, 0, flags, 0, b'')
    sock.sendto(fin_msg, addr)

    fin_ack_received = False
    while not fin_ack_received:
        sock.settimeout(0.5)
        try:
            fin_ack_msg, addr = sock.recvfrom(1472)
            header_from_msg = fin_ack_msg[:12]
            seq_num, ack_num, flags, win = parse_header(header_from_msg)
            syn, ack, fin = parse_flags(flags)

            if ack and ack_num == sent_seq_num:
                print("Received ACK msg for FIN msg with ack_num", ack_num)
                sent_seq_num += 1
                sock.close()
                fin_ack_received = True
                return

            elif not ack and ack_num < sent_seq_num:
                print("Received duplicate ACK msg with ack_num", ack_num)
                flags = 2
                fin_msg = create_packet(sent_seq_num, 0, flags, 0, b'')
                sock.sendto(fin_msg, addr)
        except timeout:
            print(f"Timeout occurred. Resending FIN msg")
            sock.sendto(fin_msg, addr)

# Metoden under tar inn filnavnet med engang, som er kanskje feil
'''def GBN(sock, addr, file_name, window_size):

    initiate_handshake(sock, addr)

    next_seq_num = 1
    base_seq_num = 1
    unacked_packets = {}

    with open(file_name, 'rb') as file:
        while True:
            while next_seq_num < base_seq_num + window_size:
                data = file.read(1460)
                if not data:
                    break

                send(sock, data, next_seq_num, addr)
                unacked_packets[next_seq_num] = data
                next_seq_num += 1


            sock.settimeout(0.5)
            try:
                ack_msg, addr = sock.recvfrom(1472)
                seq_num, ack_num, flags, win = parse_header(ack_msg[:12])
                syn, ack, fin = parse_flags(flags)

                if ack and ack_num >= base_seq_num:
                    print("ACK msg: ack_num=", ack_num)
                    base_seq_num = ack_num + 1
                    new_unacked_packets = {}
                    for seq_num, packet_data in unacked_packets.items():
                        if seq_num >= base_seq_num:
                            new_unacked_packets[seq_num] = packet_data

                    unacked_packets = new_unacked_packets

            except timeout:
                print("Timeout occurred. Resending packets")
                for seq_num, packet_data in unacked_packets.items():

                    new_packet = create_packet(seq_num, 0, 0, 0, packet_data)

                    sock.sendto(new_packet, addr)

            if not unacked_packets and not data:
                break'''

def GBN(send_sock, addr, data, window_size):

    initiate_handshake(send_sock, addr)

    next_seq_num = 1
    base_seq_num = 1
    unacked_packets = {}
    data_offset = 0

    while True:
        while next_seq_num < base_seq_num + window_size:
            chunk_size = min(1460, len(data) - data_offset)
            if chunk_size == 0:
                break

            chunk_data = data[data_offset:data_offset+chunk_size]
            send(send_sock, chunk_data, next_seq_num, addr)
            unacked_packets[next_seq_num] = chunk_data
            next_seq_num += 1
            data_offset += chunk_size

        send_sock.settimeout(0.5)
        try:
            ack_msg, addr = send_sock.recvfrom(1472)
            seq_num, ack_num, flags, win = parse_header(ack_msg[:12])
            syn, ack, fin = parse_flags(flags)

            if ack and ack_num >= base_seq_num:
                print("ACK msg: ack_num=", ack_num)
                base_seq_num = ack_num + 1
                new_unacked_packets = {}
                for seq_num, packet_data in unacked_packets.items():
                    if seq_num >= base_seq_num:
                        new_unacked_packets[seq_num] = packet_data

                unacked_packets = new_unacked_packets

        except timeout:
            print("Timeout occurred. Resending packets")
            for seq_num, packet_data in unacked_packets.items():

                new_packet = create_packet(seq_num, 0, 0, 0, packet_data)

                send_sock.sendto(new_packet, addr)





# Koden under, tar imot filnavnet med engang, noe som kanskje er feil
def RECV_GBN(sock):
    handle_handshake(sock)

    expected_seq_num = 1
    received_data = b''
    while True:
        message, addr = sock.recvfrom(1472)
        seq_num, ack_num, flags, win = parse_header(message[:12])
        syn, ack, fin = parse_flags(flags)

        if syn:
            send_ack(sock, seq_num+1, addr)
            #send_ack(sock, ack_num=seq_num+1, seq_num=expected_seq_num)

        elif not ack and seq_num >= expected_seq_num:
            if not fin and seq_num == expected_seq_num:
                print("Received in-order with seq_num=", seq_num)
                received_data += message[12:]
                expected_seq_num += 1

                # Acknowledge the last received packet
                send_ack(sock, seq_num+1, addr)
                #send_ack(sock, ack_num=seq_num+1, seq_num=expected_seq_num)
            elif fin and not ack and seq_num >= expected_seq_num:
                print("Received FIN msg with seq_num", seq_num)
                send_ack(sock, seq_num+1, addr)
                sock.close()
                return received_data
            else:
                print("Received out-of-order with seq_num=", seq_num)
                # Discard out-of-order packets
                pass
