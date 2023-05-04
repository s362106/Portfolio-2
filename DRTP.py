import time
from struct import *
from socket import *
import sys

TIMEOUT = 0.5

# Header format
header_format = '!IIHH'

handshake_complete = False


def create_packet(seq_num, ack_num, flags, window_size, data):
    """
        Creates a packet from the given parameters.

        Args:
            seq_num (int): The sequence number of the packet.
            ack_num (int): The acknowledgement number of the packet.
            flags (int): An integer representing the packet's flags.
            window_size (int): The window size of the packet.
            data (bytes): The data to be included in the packet.

        Returns:
            bytes: The packet created from the given parameters.
        """
    header = pack(header_format, seq_num, ack_num, flags, window_size)
    packet = header + data
    return packet


def parse_header(header):
    """
       Parses the given header bytes and returns the values as a tuple.

       Args:
           header (bytes): The header bytes to be parsed.

       Returns:
           tuple[int, int, int, int]: A tuple containing the sequence number, acknowledgement number, flags,
           and window size parsed from the header bytes.
       """
    header_from_msg = unpack(header_format, header)
    return header_from_msg


def parse_flags(flags):
    """
        Parses the given flags integer and returns a tuple containing the SYN, ACK, and FIN flags.

        Args:
            flags (int): An integer representing the flags of the packet.

        Returns:
            tuple[int, int, int]: A tuple containing the SYN, ACK, and FIN flags.
        """
    syn = (flags >> 3) & 1
    ack = (flags >> 2) & 1
    fin = (flags >> 1) & 1

    return syn, ack, fin


def send(sock, data, seq_num, addr):
    """
        Sends a packet with the given data, sequence number, and address using the provided socket.

        Args:
            sock (socket): The socket to use for sending the packet.
            data (bytes): The data to include as payload in the packet.
            seq_num (int): The sequence number of the packet.
            addr (tuple): A tuple representing the address to send the packet to.

        Returns:
            None.
        """
    packet = create_packet(seq_num, 0, 0, 0, data)
    sock.sendto(packet, addr)


def send_ack(sock, ack_num, addr):
    """
        Sends an acknowledgement packet with the given acknowledgement number and address using the provided socket.

        Args:
            sock (socket): The socket to use for sending the acknowledgement packet.
            ack_num (int): The acknowledgement number to include in the packet.
            addr (tuple): A tuple representing the address to send the acknowledgement packet to.

        Returns:
            None.
        """

    ack_msg = create_packet(0, ack_num, 4, 64, b'')     # flags = 0 1 0 0 = 4 --> ACK flag value
    sock.sendto(ack_msg, addr)


def initiate_handshake(sock, addr):
    global handshake_complete

    # If handshake has not yet been completed, establish connection
    if not handshake_complete:
        flags = 8  # 1 0 0 0 = SYN flag value
        syn_packet = create_packet(0, 0, flags, 0, b'')  # Create SYN packet
        sock.sendto(syn_packet, addr)  # Send SYN packet to destination address
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


def close_conn(sock, addr, next_seq_num):
    flags = 2
    fin_msg = create_packet(next_seq_num, 0, flags, 0, b'')
    sock.sendto(fin_msg, addr)

    fin_ack_received = False
    while not fin_ack_received:
        sock.settimeout(0.5)
        try:
            fin_ack_msg, addr = sock.recvfrom(1472)
            header_from_msg = fin_ack_msg[:12]
            seq_num, ack_num, flags, win = parse_header(header_from_msg)
            syn, ack, fin = parse_flags(flags)

            if ack and ack_num == next_seq_num:
                print("Received ACK msg for FIN msg with ack_num", ack_num)
                next_seq_num += 1
                sock.close()
                fin_ack_received = True
                return

            elif not ack and ack_num < next_seq_num:
                print("Received duplicate ACK msg with ack_num", ack_num)
                flags = 2
                fin_msg = create_packet(next_seq_num, 0, flags, 0, b'')
                sock.sendto(fin_msg, addr)
        except timeout:
            print(f"Timeout occurred. Resending FIN msg")
            sock.sendto(fin_msg, addr)


# server
def RECV_STOP(sock, skip_ack):
    handle_handshake(sock)
    expected_seq_num = 1
    received_data = b''

    while True:
        msg, addr = sock.recvfrom(1472)

        header_from_msg = msg[:12]
        seq_num, ack_num, flags, win = parse_header(header_from_msg)
        syn, ack, fin = parse_flags(flags)

        if skip_ack:
            print("Skipping first ACK msg")
            skip_ack = False
            continue

        if not fin and not syn and not ack and seq_num == expected_seq_num:
            print(f"Received packet with seq_num", seq_num)
            app_data = msg[12:]
            send_ack(sock, expected_seq_num, addr)
            print("Sent ACK msg with ack_num", expected_seq_num)
            expected_seq_num += 1
            received_data += app_data

        elif not fin and not syn and not ack and seq_num != expected_seq_num:
            if seq_num == expected_seq_num - 1:
                print(f"Received duplicate packet with seq_num", seq_num)
                send_ack(sock, expected_seq_num - 1, addr)

            else:
                print("Received out-of-order packet. Ignoring")

        if fin and not ack and not syn and seq_num == expected_seq_num:
            print("FIN msg received with seq_num", seq_num)
            flags = 4
            send_ack(sock, expected_seq_num, addr)
            sock.close()
            return received_data

# client
def SEND_SAW(sock, addr, data):
    # If handshake has not yet been completed, establish connection
    initiate_handshake(sock, addr)

    sequence_num = 1
    while True:
        if not data:
            close_conn(sock, addr, sequence_num)
            break

        # Send data packet with current sequence number
        send(sock, data[:1460], sequence_num, addr)
        data = data[1460:]

        # Wait for ACK message from the receiver
        received_ack = False
        while not received_ack:
            # Set a timeout of 0.5 seconds for the socket for receiving ACK message
            sock.settimeout(0.5)

            try:
                ack_msg, addr = sock.recvfrom(1472)  # Receive message from destination address
                header_from_msg = ack_msg[:12]  # Extract the header from the received message
                seq_num, ack_num, flags, win = parse_header(header_from_msg)  # Parse the header fields
                syn, ack, fin = parse_flags(flags)  # Parse the flags

                # If received ACK message is valid, update global sequence number and set received_ack to True
                if ack and ack_num == sequence_num:
                    print(f"ACK msg: ack_num={ack_num}, flags={flags}")
                    sequence_num += 1
                    received_ack = True

                # Else if received duplicate ACK message
                elif ack and ack_num == sequence_num - 1:
                    print("Received duplicate ACK msg with ack_num", ack_num)
                    send(sock, data[:1460], sequence_num - 1, addr)

            except timeout:
                print(f"Timeout occurred. Resending packet with seq_num={sequence_num}, flags=0")
                send(sock, data[:1460], sequence_num, addr)


# server
def RECV_GBN(sock, skip_ack):
    handle_handshake(sock)

    expected_seq_num = 1
    received_data = b''
    while True:
        message, addr = sock.recvfrom(1472)
        seq_num, ack_num, flags, win = parse_header(message[:12])
        syn, ack, fin = parse_flags(flags)

        if skip_ack:
            skip_ack = False
            print("Skipping first ACK msg")
            continue

        if syn:
            handle_handshake(sock)
            # send_ack(sock, ack_num=seq_num+1, seq_num=expected_seq_num)

        elif not ack and seq_num >= expected_seq_num:
            if not fin and seq_num == expected_seq_num:
                print("Received in-order with seq_num=", seq_num)
                received_data += message[12:]
                expected_seq_num += 1

                # Acknowledge the last received packet
                send_ack(sock, seq_num, addr)
                # send_ack(sock, ack_num=seq_num+1, seq_num=expected_seq_num)
            elif fin and not ack and seq_num == expected_seq_num:
                print("Received FIN msg with seq_num", seq_num)
                send_ack(sock, seq_num, addr)
                sock.close()
                return received_data
            else:
                print("Received out-of-order with seq_num=", seq_num)
                # Discard out-of-order packets
                pass

# client
def SEND_GBN(send_sock, addr, data, window_size, skip_seq_num):
    initiate_handshake(send_sock, addr)

    next_seq_num = 1
    base_seq_num = 1
    unacked_packets = {}
    data_offset = 0
    fin_sent = False

    while not fin_sent:
        while next_seq_num < base_seq_num + window_size:
            chunk_size = min(1460, len(data) - data_offset)
            if chunk_size == 0:
                if not unacked_packets:
                    # All sent packets have been acknowledged, send FIN message
                    fin_packet = create_packet(next_seq_num, 0, 2, 0, b'')
                    send_sock.sendto(fin_packet, addr)
                    print("FIN msg sent. Waiting for ACK...")
                    fin_sent = True
                    break
                else:
                    break

            chunk_data = data[data_offset:data_offset + chunk_size]
            if skip_seq_num and next_seq_num == 5:
                skip_seq_num = False
                print("Skipping seq_num =", next_seq_num)
                next_seq_num += 1
                data_offset += chunk_size
                unacked_packets[5] = chunk_data
                continue

            send(send_sock, chunk_data, next_seq_num, addr)
            unacked_packets[next_seq_num] = chunk_data
            next_seq_num += 1
            data_offset += chunk_size

        if not fin_sent:
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

    # Wait for ACK for the FIN message
    while True:
        send_sock.settimeout(0.5)
        try:
            ack_msg, addr = send_sock.recvfrom(1472)
            seq_num, ack_num, flags, win = parse_header(ack_msg[:12])
            syn, ack, fin = parse_flags(flags)

            if ack and ack_num == next_seq_num:
                print("ACK for FIN msg received. Exiting...")
                break

        except timeout:
            print("Timeout occurred while waiting for ACK for FIN msg. Exiting...")
            break


# server
def recv_sr(sock, skip_ack, window_size):
    handle_handshake(sock)

    expected_seq_num = 1
    received_data = b''
    base_seq_num = 1
    unacked_packets = {}

    while True:
        message, addr = sock.recvfrom(1472)
        seq_num, ack_num, flags, win = parse_header(message[:12])
        syn, ack, fin = parse_flags(flags)

        if skip_ack:
            skip_ack = False
            print("Skipping first ACK msg")
            continue

        if syn:
            handle_handshake(sock)

        elif not ack and seq_num >= expected_seq_num and len(unacked_packets) < window_size:
            if not fin and seq_num == expected_seq_num:
                print("Received in-order with seq_num=", seq_num)
                received_data += message[12:]
                expected_seq_num += 1

                # Acknowledge the last received packet
                send_ack(sock, seq_num, addr)

                # Send acknowledgments for any other received but unacknowledged packets
                while expected_seq_num in unacked_packets:
                    received_data += unacked_packets[expected_seq_num]
                    expected_seq_num += 1
                    del unacked_packets[expected_seq_num - 1]
                    send_ack(sock, expected_seq_num - 1, addr)
            elif fin and not ack and seq_num == expected_seq_num:
                print("Received FIN msg with seq_num", seq_num)
                send_ack(sock, seq_num, addr)
                sock.close()
                return received_data
            else:
                print("Received out-of-order with seq_num=", seq_num)
                # Send an acknowledgment for the last received in-order packet
                send_ack(sock, expected_seq_num - 1, addr)

                # Add the out-of-order packet to the unacknowledged list
                unacked_packets[seq_num] = message[12:]

                # Send acknowledgments for any other received but unacknowledged packets in order
                while expected_seq_num in unacked_packets:
                    received_data += unacked_packets[expected_seq_num]
                    expected_seq_num += 1
                    del unacked_packets[expected_seq_num - 1]
                    send_ack(sock, expected_seq_num - 1, addr)


def send_sr(send_sock, addr, data, window_size):
    # Establish a connection with the server
    initiate_handshake(send_sock, addr)

    # Initialize variables
    next_seq_num = 1
    base_seq_num = 1
    unacked_packets = {}
    data_offset = 0
    fin_sent = False

    while not fin_sent:
        # Send packets within the window
        while next_seq_num < base_seq_num + window_size:
            chunk_size = min(1460, len(data) - data_offset)
            if chunk_size == 0:
                if not unacked_packets:
                    # All data has been sent and acknowledged, send FIN message
                    fin_packet = create_packet(next_seq_num, 0, 2, 0, b'')
                    send_sock.sendto(fin_packet, addr)
                    print("FIN msg sent. Waiting for ACK...")
                    fin_sent = True
                    break
                else:
                    break

            # Create packet and send it
            chunk_data = data[data_offset:data_offset + chunk_size]
            send_packet = create_packet(next_seq_num, 0, 0, 0, chunk_data)
            send_sock.sendto(send_packet, addr)

            # Add packet to unacked packets and update next_seq_num and data_offset
            unacked_packets[next_seq_num] = (send_packet, time.monotonic())
            next_seq_num += 1
            data_offset += chunk_size

        if not fin_sent:
            # Check for ACKs
            send_sock.settimeout(0.5)
            try:
                ack_packet, addr = send_sock.recvfrom(1472)
                ack_seq_num, ack_num, ack_flags, ack_win = parse_header(ack_packet[:12])
                ack_syn, ack, ack_fin = parse_flags(ack_flags)

                if ack and ack_num >= base_seq_num:
                    print("ACK msg: ack_num=", ack_num)
                    # Update base_seq_num and remove acknowledged packets from unacked_packets
                    base_seq_num = ack_num + 1
                    for seq_num in list(unacked_packets.keys()):
                        if seq_num < base_seq_num:
                            unacked_packets.pop(seq_num)

            except timeout:
                print("Timeout occurred. Resending packets")
                # Resend unacknowledged packets that have timed out
                current_time = time.monotonic()
                for seq_num, packet_info in unacked_packets.items():
                    packet, timestamp = packet_info
                    if current_time - timestamp >= 0.5:
                        send_sock.sendto(packet, addr)
                        unacked_packets[seq_num] = (packet, current_time)

    # Wait for ACK for the FIN message
    while True:
        send_sock.settimeout(0.5)
        try:
            ack_packet, addr = send_sock.recvfrom(1472)
            ack_seq_num, ack_num, ack_flags, ack_win = parse_header(ack_packet[:12])
            ack_syn, ack, ack_fin = parse_flags(ack_flags)

            if ack and ack_num == next_seq_num:
                print("ACK for FIN msg received. Exiting...")
                break

        except timeout:
            print("Timeout occurred while waiting for ACK for FIN msg. Exiting...")
            break