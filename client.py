import socket
import threading
import struct
import time

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4
UDP_PORT = 13117
BUFFER_SIZE = 1024

def recive_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.bind(('', UDP_PORT))
    print(f"Client started, listening for offer requests...")
    while True:
        data, server_address = udp_socket.recvfrom(BUFFER_SIZE)
        magic_cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', data)
        if magic_cookie == MAGIC_COOKIE and message_type == OFFER_TYPE:
            print(f"Received offer: TCP port {tcp_port}, UDP port {udp_port}")
            return server_address[0],udp_port,tcp_port

def send_tcp_request(server_address, tcp_port, size):
    try:
        start = time.time()
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_address, tcp_port))
        tcp_socket.sendall(f"{size}\n".encode('utf-8'))
        received = 0
        while received < size:
            received += len(tcp_socket.recv(BUFFER_SIZE))
        interval= (time.time() - start)
        speed = (size * 8) / interval
        print(f"TCP transfer finished, total time: {interval:.2f} seconds, total speed: {speed:.2f} bits/second")
    except Exception as e:
        print(f"TCP test error: {e}")

def send_udp_request(server_address, udp_port, size):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1)
    udp_socket.sendto(struct.pack("!IBQ", MAGIC_COOKIE, REQUEST_TYPE, size), (server_address, udp_port))

    received = 0
    start_time = time.time()

    while True:
        try:
            data, _ = udp_socket.recvfrom(BUFFER_SIZE + 20)
            magic_cookie, message_type, total_segments, segment = struct.unpack("!IBQQ", data[:21])
            if magic_cookie == MAGIC_COOKIE and message_type == PAYLOAD_TYPE:
                if segment <= total_segments:
                    received += 1
                print(f"received {segment + 1}/{total_segments}")
        except socket.timeout:
            break
    interval = time.time() - start_time
    success = (received / total_segments) * 100
    speed = (received * BUFFER_SIZE * 8) / interval
    print(f"UDP Complete: Time: {interval:.2f}s, total speed: {speed:.2f} bits/s, percentage of packets received successfully: {success:.2f}%")

def main():
    while True:
        server_address, udp_port, tcp_port = recive_offers()
        fileSize=int(input("Enter the file size: "))
        tcp_conn=int(input("Enter the number of TCP connections: "))
        udp_conn=int(input("Enter the number of UDP connections: "))
        threads=[]
        for i in range(tcp_conn):
            t=threading.Thread(target=send_tcp_request, args=(server_address, tcp_port, fileSize))
            t.start()
            threads.append(t)
        for i in range(udp_conn):
            t=threading.Thread(target=send_udp_request, args=(server_address, udp_port, fileSize))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()

        print("All transfers complete.")
    
if __name__ == "__main__":
    main()