import os, socket, threading, time
from monitoring.monitor import Monitor

IP, PORT, MAX_CLIENTS = "127.0.0.1", 5000, 4
FILES_DIR = os.path.join(os.path.dirname(__file__), '..', 'server_files')
os.makedirs(FILES_DIR, exist_ok=True)
ADMIN_PASS = "adminpass"
STATS_FILE = os.path.join(os.path.dirname(__file__), '..', 'monitoring', 'server_stats.txt')
UPDATE_INTERVAL, TIMEOUT_SECONDS = 5, 60

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()
print(f"Server listening on {IP}:{PORT}")

client_sockets, client_meta = {}, {}
lock = threading.Lock()
monitor = Monitor(STATS_FILE, UPDATE_INTERVAL, TIMEOUT_SECONDS)

def close_socket(sock_id):
    with lock:
        sock = client_sockets.pop(sock_id, None)
        client_meta.pop(sock_id, None)
    if sock:
        try: sock.shutdown(socket.SHUT_RDWR); sock.close()
        except: pass
        print(f"Socket {sock_id} closed (timeout).")

monitor.start(close_callback=lambda sock_id: close_socket(sock_id))
threading.Thread(target=monitor.admin_console_loop, daemon=True).start()

def list_files(): 
    return "\n".join(os.listdir(FILES_DIR)) + "\n" if os.listdir(FILES_DIR) else "Nuk ka file.\n"

def read_file(f):
    path = os.path.join(FILES_DIR,f)
    return open(path,"r",encoding="utf-8").read()+"\n" if os.path.exists(path) else "File nuk ekziston.\n"

def delete_file(f):
    path = os.path.join(FILES_DIR,f)
    if os.path.exists(path):
        os.remove(path)
        return f"File '{f}' u fshi.\n"
    else:
        return "File nuk ekziston.\n"

def info_file(f):
    path = os.path.join(FILES_DIR,f)
    if os.path.exists(path):
        return f"{f} size={os.path.getsize(path)} bytes\n"
    else:
        return "File nuk ekziston.\n"

def upload_file(f, content):
    path = os.path.join(FILES_DIR,f)
    with open(path, 'w', encoding='utf-8') as fp:
        fp.write(content)
    return f"File '{f}' u upload-ua.\n"

def download_file(f):
    path = os.path.join(FILES_DIR,f)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as fp:
            return fp.read()
    else:
        return "File nuk ekziston.\n"

def search_files(keyword):
    result = [f for f in os.listdir(FILES_DIR) if keyword.lower() in f.lower()]
    return "\n".join(result) + "\n" if result else "Nuk u gjet asnjë file.\n"

def safe_send(sock, data): 
    try: sock.sendall(data)
    except: sock.close()