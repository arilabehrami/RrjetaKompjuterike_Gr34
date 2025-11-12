import os
import socket


IP = "127.0.0.1"      
PORT = 5000          
MAX_CLIENTS = 4       


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


server_socket.bind((IP, PORT))
server_socket.listen()
print(f"Serveri është duke dëgjuar në {IP}:{PORT}")


clients = []  


while True:
    conn, addr = server_socket.accept()  
    print(f"Klient i ri nga: {addr}")


    if len(clients) >= MAX_CLIENTS:
        print(" Serveri është plot. Lidhja u refuzua.")
        conn.send("Serveri është plot. Provo më vonë.\n")
        conn.close()
        continue

    clients.append(addr)
    print(f"Lidhje aktive: {len(clients)} klientë")


    conn.send(b"Pershendetje! Je lidhur me serverin.\n")

    conn.close()


FILES_DIR = "server_files"
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

