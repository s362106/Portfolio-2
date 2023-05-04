# Portfolio-2

There are two programs in this Portfolio. The first program, DRTP.py, is a custom reliable transfer protocol that is built on UDP. This protocol ensures all packets are delivered in-order, without loss and duplicates. The second program, application.py is a client/server program that uses the custom reliable transfer protocol, DRTP, to send a file between two end hosts. Both programs are built with python3.

## How to run the program

1. You need to have installed Python3.
2. Then open your terminal, go to the directory where *application.py* and *DRTP.py* are located.

You can run *application.py* in server/receiver mode with the default options with the following command:
 - ```python3 application.py -s```

*Note that by default, **application.py** uses the Stop_And_Wait protocol to send and receive the file.*

To operate *application.py* in client/sender mode, it can be invoked as follows:
 - ```python3 application.py -c -i <server_ip> -ip <server_port>```

### Optional arguments

Below are the optional arguments you can use when running the program:

- **-s, --server**
    - Run in server/receiver mode

- **-c, --client**
    - Run in client/sender mode

- **-i, --ip_address**
    - IP address to use when running the program (default: 127.0.0.1)

- **-p, --port**
    - Port number of the server (default: 12000)

- **-f, --file_name**
    - Name of the file to be sent

- **-r, --reliability**
    - Choose which reliable protocol to use when sending and receiving the file (default: Stop_And_Wait)

- **-t, --test**
    - Test protocol for skip_ack(in server mode) or loss(in client mode)

- **-w, --window**
    - Window size for the Go_Back_N and Selective Repeate protocols (default: 5)

## How to generate data

To test the program, you have to first run the program in server mode:
```
python3 application.py -s
```
Afterward, open a new terminal window and run *application.py* in client mode:
```
python3 application.py -c
```

The client will send the default file using the Stop_And_Wait reliable method

### Testing for retransmission scenarios

To skip an acknowledgment message and therefore trigger retransmission, use the following command:
```
python3 application.py -s -r <reliable method> -t skip_ack
```

This test works for all three reliable methods.

To skip a sequence number to show the out-of-order delivery effect, and trigger retransmission, use the following command:
```
python3 application.py -c -r <reliable_method> -t loss
```
*Note that this test only works for Go_Back_N and Selective Repeate reliable methods*
