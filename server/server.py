import os
import socket

import threading
from monitoring.monitor import Monitor

IP = "127.0.0.1"      
PORT = 5000          
MAX_CLIENTS = 4       

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP, PORT))
server_socket.listen()
print(f"Serveri është duke dëgjuar në {IP}:{PORT}")

clients = []  

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

client_sockets = {}
client_lock = threading.Lock()
def close_socket_by_id(sock_id):
   
    with client_lock:
        sock = client_sockets.get(sock_id)
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
           
            del client_sockets[sock_id]
          
            print(f"[Monitor callback] Socket with id {sock_id} was closed due to timeout.")

STATS_FILE = 'monitoring/server_stats.txt'
UPDATE_INTERVAL = 5         
TIMEOUT_SECONDS = 60       

monitor = Monitor(stats_file_path=STATS_FILE, update_interval=UPDATE_INTERVAL, timeout_seconds=TIMEOUT_SECONDS)
monitor.start(close_callback=close_socket_by_id)


admin_thread = threading.Thread(target=monitor.admin_console_loop, daemon=True)
admin_thread.start()


while True:
    conn, addr = server_socket.accept()  
    print(f"Klient i ri nga: {addr}")

    if len(clients) >= MAX_CLIENTS:
        print("Serveri është plot. Lidhja u refuzua.")
        conn.send("Serveri është plot. Provo më vonë.\n".encode('utf-8'))
        conn.close()
        continue

     sock_id = id(conn)
    with client_lock:
        client_sockets[sock_id] = conn
    monitor.register(sock_id, addr)   

    clients.append(addr)
    print(f"Lidhje aktive: {len(clients)} klientë")

    conn.send("Përshëndetje! Je lidhur me serverin.\n".encode('utf-8'))
    conn.send("Shkruaj komandë: /list, /read <file>, /upload <file> <text>, /download <file>, /delete <file>, /info <file>\n".encode('utf-8'))

    try:
        data = conn.recv(4096).decode().strip()
        if not data:
             try:
                monitor.unregister(sock_id)
            except Exception:
                pass
            with client_lock:
                client_sockets.pop(sock_id, None)

            conn.close()
            continue

            try:
                  monitor.record_received(sock_id, len(data.encode('utf-8')))
            except Exception:
                pass

        print(f"[{addr}] -> {data}")
        parts = data.split(" ", 2)
        cmd = parts[0]

        if cmd == "/list":
            response = list_files()
        elif cmd == "/read" and len(parts) > 1:
            response = read_file(parts[1])
        elif cmd == "/upload" and len(parts) > 2:
            response = upload_file(parts[1], parts[2])
        elif cmd == "/download" and len(parts) > 1:
            response = download_file(parts[1])
        elif cmd == "/delete" and len(parts) > 1:
            response = delete_file(parts[1])
        elif cmd == "/info" and len(parts) > 1:
            response = info_file(parts[1])
        else:
            response = "Komandë e panjohur ose parametra të munguar.\n"

        conn.send(response.encode('utf-8'))

    except Exception as e:
                try:
            monitor.unregister(sock_id)
        except Exception:
            pass
        with client_lock:
            client_sockets.pop(sock_id, None)
         try: 
        conn.send(f"Gabim: {e}\n".encode('utf-8'))
         except Exception:
            pass

         try:
             monitor.unregister(sock_id)
        except Exception:
            pass
    with client_lock:
        client_sockets.pop(sock_id, None)
    
    try:
        if addr in clients:
            clients.remove(addr)
    except Exception:
        pass
    


    conn.close()
    print(f"Klienti {addr} u shkëput.")
