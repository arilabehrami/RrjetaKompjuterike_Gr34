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

monitor.start(close_callback=lambda sock_id: close_client(sock_id))
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

def handle_client(conn, addr):
    sock_id = id(conn)
    with lock: 
        client_sockets[sock_id] = conn
        client_meta[sock_id] = {'role':'user', 'addr':addr}
    monitor.register(sock_id, addr)
    safe_send(conn, b"Welcome! ROLE user/admin <pass>. Commands: /list, /read <file>, /upload <file> <text>, /delete <file>, /info <file>, /download <file>, /search <keyword>\n")

    while True:
        try: data = conn.recv(8192)
        except: break
        if not data: break
        monitor.record_received(sock_id, len(data))
        text = data.decode('utf-8', errors='ignore').strip()
        if not text: continue
        cmd,*args = text.split(" ",1)
        role = client_meta[sock_id]['role']

        if cmd.lower()=="role":
            parts = args[0].split() if args else []
            r = parts[0].lower() if len(parts) > 0 else "user"
            passwd = parts[1] if len(parts) > 1 else ""
            if r=="admin" and passwd==ADMIN_PASS:
                role='admin'
            client_meta[sock_id]['role'] = role
            safe_send(conn, f"Assigned role: {role}\n".encode())
            continue

        response = "Komandë e panjohur.\n"
        try:
            if cmd=="/list":
                response = list_files()
            elif cmd=="/read" and args:
                response = read_file(args[0])
            elif cmd=="/delete" and args:
                if role=="admin":
                    response = delete_file(args[0])
                else:
                    response = "Nuk ke privilegje për këtë komandë.\n"
            elif cmd=="/info" and args:
                response = info_file(args[0])
            elif cmd=="/upload" and args:
                if role=="admin":
                    file_name, content = args[0].split(" ",1)
                    response = upload_file(file_name, content)
                else:
                    response = "Nuk ke privilegje për këtë komandë.\n"
            elif cmd=="/download" and args:
                response = download_file(args[0])
            elif cmd=="/search" and args:
                response = search_files(args[0])
            elif cmd=="/stats" and role=="admin":
                monitor.print_stats_to_console()
                response="STATS shfaqur\n"
        except Exception as e:
            response=f"Gabim: {e}\n"

        safe_send(conn, (response + "\n").encode())

    close_socket(sock_id)
    print(f"Klienti {addr} shkëput.")

def accept_loop():
    while True:
        try: conn, addr = server_socket.accept()
        except: continue
        with lock:
            if len(client_sockets) >= MAX_CLIENTS:
                safe_send(conn,b"Server full.\n")
                conn.close()
                continue
        print(f"New client {addr}")
        threading.Thread(target=handle_client,args=(conn,addr),daemon=True).start()

def close_client(sock_id):
    try:
        sock = client_sockets[sock_id]
        sock.close()
    except:
        pass
    finally:
        monitor.unregister(sock_id)



if __name__=="__main__":
    print("Server running...")
    accept_loop()
