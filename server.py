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

def list_files():
    files = os.listdir(FILES_DIR)
    if not files:
        return "Nuk ka asnjë file në server.\n"
    return "\n".join(files) + "\n"


def read_file(filename):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return "File nuk ekziston.\n"
    with open(path, "r", encoding="utf-8") as f:
        return f.read() + "\n"


def upload_file(filename, content):
    path = os.path.join(FILES_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File '{filename}' u ngarkua me sukses.\n"


def download_file(filename):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return "File nuk ekziston.\n"
    with open(path, "r", encoding="utf-8") as f:
        return f.read() + "\n"


def delete_file(filename):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return "File nuk ekziston.\n"
    os.remove(path)
    return f"File '{filename}' u fshi me sukses.\n"


def info_file(filename):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return "File nuk ekziston.\n"
    size = os.path.getsize(path)
    return f"Emri: {filename}\nMadhësia: {size} bytes\n"