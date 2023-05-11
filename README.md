# Portfolio-2

There are two programs in this Portfolio. The first program, `DRTP.py`, is a custom reliable transfer protocol that is built on UDP. This protocol ensures all packets are delivered in-order, without loss and duplicates. The second program, `application.py` is a client/server program that uses the custom reliable transfer protocol, DRTP, to send a file between two end hosts. Both programs are built with python3.

The three reliability functions are:
1. `SAW`, *Stop-And-Wait protocol*: 
    - The sender sends a packet and waits for an ACK. If an ACK is received, it sends a new packet. If not, it waits for a timeout and then resends the packet. If the sender receives a duplicate ACK, it resends the packet.
2. `GBN`, *Go-Back-N protocol*:
    - The sender uses a fixed window size of 5 packets to transfer data, where the sequence numbers represent the packets (packet 1 = 1, packet 2 = 2, etc.). If no ACK packet is received before timeout, all unacknowledged packets are assumed to be lost and are retransmitted. The receiver processes incoming packets in order, and any out-of-order packets indicate packet loss or reordering in the network. In such cases, the DRTP receiver does not acknowledge or process the packets and may discard them.
3. `SR`, *Selective-Repeat protocol*:
    - Based of Go-Back-N protocol, but it differs in that it does not discard out-of-order packets. Instead, it places them in the correct location in the receive buffer. 

# How to run the program

1. You need to have installed Python3.
2. Then open your terminal, go to the directory where `application.py` and `DRTP.py` are located.

## Server mode
To run `application.py` in server/receiver mode with the default options, it can be invoked as:

    python3 application.py -s

* `-s, --server`: run in server mode; receives a file and writes to the files system

To run the server/receiver mode with the all the available options, it can be invoked as:

    python3 application.py -s -i <ip_address> -p <port_number> -r <reliable_method> -t <test_case>

* `-i, --ip_address`: the IP address to bind the server to (default: `127.0.0.1`)
* `-p, --port`: the port number to listen for incoming connections (default: `12000`)
* `-r, --reliability`: the reliability function, the available options are `SAW`, `GBN` and `SR`,  (default: `SAW`)
* `-t, --test`: the test protocol to skip an ack to trigger retransmission at the clien/sender-side (e.g. `skip_ack`)

## Client mode
To operate `application.py` in client/sender mode with the default options, it can be invoked as follows:

    python3 application.py -c

* `-c, --client`: run in client mode; reads file from computer and sends it over DRTP/UDP

To run the client/sender mode with the all the available options, it can be invoked as:

    python3 application.py -c -i <ip_address> -p <port_number> -f <file_to_transfer.jpg> -r <reliable_method> -w <window_size> -t <test_case>

* `-i, --ip_address`: the IP address to bind the server to (default: `127.0.0.1`)
* `-p, --port`: the port number to listen for incoming connections (default: `12000`)
* `-f, --file_name`: the name of the file to send over (default: `./testFile.jpg`)
* `-r, --reliability`: the reliability function, the available options are `SAW`, `GBN` and `SR`,  (default: `SAW`)
* `-t, --test`: the test protocol to test packet loss scenario (e.g. `loss`)
* `-w, --window`: the window size for the `GBN` and `SR` protocols (default: `5`)

> **NOTE** The server and client ***MUST*** use the same reliability_method

# How to generate data

To test the program, you have to first run the program in server mode:

    python3 application.py -s

Afterward, open a new terminal window and run *application.py* in client mode:

    python3 application.py -c


The client will send the default file using the Stop_And_Wait reliable method.

## Testing for retransmission scenarios

To skip an acknowledgment message at the receiver side and trigger retransmission, use the following command:

    python3 application.py -s -r <reliable method> -t skip_ack


> **NOTE** This test works for all three reliable methods.

To skip a sequence number at the sender side to show the out-of-order delivery effect, and trigger retransmission, use the following command:

    python3 application.py -c -r <reliable_method> -t loss

> **NOTE** This test only works for the `GBN` and `SR` reliable methods.
