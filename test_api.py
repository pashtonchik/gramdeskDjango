import socket
import sys
import os

HOST = "127.0.0.1"
PORT = 8000
BUF_SIZE = 512
DOWNLOAD_DIR = "downloads"

def send_file(conn, file_name):

    total_sent = 0
    with open('017-4852450_5920950975.pdf', 'rb') as output:
        while True:
            data = output.read(BUF_SIZE)
            if not data:
                break
            conn.sendall(data)
            print('отпрауили кусок')
            total_sent += len(data)

    print("finished sending", total_sent, "bytes")
    return True

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect((HOST, PORT))
except Exception as e:
    print("cannot connect to server:", e, file=sys.stderr)

file_name = input("\nFile to get: ")
if not file_name:
    sock.close()

err = send_file(sock, file_name)
if err:
    print(err, file=sys.stderr)
sock.close()
