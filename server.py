import socket
import threading
import time
import struct
import os

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4
OFFER_INTERVAL = 1  # seconds
TCP_PORT = 12345
UDP_PORT = 13117
BUFFER_SIZE = 1024

def send_offer_messages():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        udp_socket.sendto(struct.pack('!IBHH', MAGIC_COOKIE, OFFER_TYPE, UDP_PORT, TCP_PORT), ('<broadcast>', UDP_PORT))
        time.sleep(OFFER_INTERVAL)

def handle_tcp(client_socket, client_address):
    data = client_socket.recv(BUFFER_SIZE).decode('utf-8').strip()
    print(f"Handling TCP client {client_address[0]}: {int(data)} bytes")
    sent=0
    while sent < int(data):
        sent += client_socket.send(b'X' * min(int(data) - sent, BUFFER_SIZE))
    print(f"Sent {sent} bytes by TCP to {client_address[0]}")

    client_socket.close()

def handle_request(udp_socket, client_address, size):
    total_segments = size // BUFFER_SIZE + 1
    for segment in range(total_segments):
        payload = struct.pack('!IBQQ', MAGIC_COOKIE, PAYLOAD_TYPE, total_segments, segment) + b'X' * BUFFER_SIZE
        udp_socket.sendto(payload,client_address)

def handle_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.bind(('', UDP_PORT))
    while True:
        data, client_address = udp_socket.recvfrom(BUFFER_SIZE)
        if(len(data)<13):
            continue
        magic_cookie, mType,size = struct.unpack('!IBQ', data)
        if magic_cookie == MAGIC_COOKIE and mType == REQUEST_TYPE:
            print(f"Received request from {client_address[0]}: {size} bytes")
            handle_request(udp_socket, client_address, size)
        else:
            print(f"Received invalid request from {client_address[0]}")

def tcp_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('0.0.0.0', TCP_PORT))
    tcp_socket.listen()
    print(f"Server started, listening on IP address {socket.gethostbyname(socket.gethostname())}")
    while True:
        client_socket, client_address = tcp_socket.accept()
        threading.Thread(target=handle_tcp, args=(client_socket, client_address)).start()


if __name__ == "__main__":
    threading.Thread(target=send_offer_messages).start()
    threading.Thread(target=handle_udp).start()
    threading.Thread(target=tcp_server).start()