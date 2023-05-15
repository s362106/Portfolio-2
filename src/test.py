import socket
import argparse

from src.DRTP import *
import threading

def test_packet_loss():
    data = open('./testFile.jpg', 'rb').read()
    window_size = 10
    ip_address = gethostbyname(gethostname())
    addr = (ip_address, 12000)

    server_sock = socket(AF_INET, SOCK_DGRAM)
    server_sock.bind(addr)

    client_sock = socket(AF_INET, SOCK_DGRAM)

    t = threading.Thread(target=SEND_GBN, args=(client_sock, addr, data, window_size, False))
    t.start()
    received_data = RECV_GBN(server_sock, True)

    assert received_data == data

test_packet_loss()