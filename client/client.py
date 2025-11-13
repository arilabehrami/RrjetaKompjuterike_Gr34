import socket
import time

IP = "127.0.0.1"  
PORT = 5000    



def connect_to_server():
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))
        print(f"\n Lidhja me serverin {IP}:{PORT} u krye me sukses.\n")

        
        print(client_socket.recv(4096).decode(), end="")
        print(client_socket.recv(4096).decode(), end="")
        return client_socket
    except Exception as e:
        print(f" Nuk u arrit lidhja me serverin: {e}")
        return None
