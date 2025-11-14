import os, socket, threading, time
from monitoring.monitor import Monitor

IP, PORT, MAX_CLIENTS = "127.0.0.1", 5000, 4
FILES_DIR = "server_files"
os.makedirs(FILES_DIR, exist_ok=True)
ADMIN_PASS = "adminpass"
STATS_FILE = 'monitoring/server_stats.txt'
UPDATE_INTERVAL, TIMEOUT_SECONDS = 5, 60

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()
print(f"Server listening on {IP}:{PORT}")

client_sockets, client_meta = {}, {}
lock = threading.Lock()
monitor = Monitor(STATS_FILE, UPDATE_INTERVAL, TIMEOUT_SECONDS)
monitor.start(close_callback=lambda sock_id: close_socket(sock_id))
threading.Thread(target=monitor.admin_console_loop, daemon=True).start()

def close_socket(sock_id):
    with lock:
        sock = client_sockets.pop(sock_id, None)
        client_meta.pop(sock_id, None)
    if sock:
        try: sock.shutdown(socket.SHUT_RDWR); sock.close()
        except: pass
        print(f"Socket {sock_id} closed (timeout).")

def list_files(): return "\n".join(os.listdir(FILES_DIR)) + "\n" if os.listdir(FILES_DIR) else "Nuk ka file.\n"
def read_file(f): return open(os.path.join(FILES_DIR,f),"r",encoding="utf-8").read()+"\n" if os.path.exists(os.path.join(FILES_DIR,f)) else "File nuk ekziston.\n"
def delete_file(f): os.remove(os.path.join(FILES_DIR,f)); return f"File '{f}' u fshi.\n" if os.path.exists(os.path.join(FILES_DIR,f)) else "File nuk ekziston.\n"
def info_file(f): p=os.path.join(FILES_DIR,f); return f"{f} size={os.path.getsize(p)} bytes\n" if os.path.exists(p) else "File nuk ekziston.\n"

def safe_send(sock, data): 
    try: sock.sendall(data)
    except: sock.close()

def handle_client(conn, addr):
    sock_id = id(conn)
    with lock: client_sockets[sock_id]=conn; client_meta[sock_id]={'role':'user','addr':addr}
    monitor.register(sock_id, addr)
    safe_send(conn, b"Welcome! ROLE user/admin <pass>. Commands: /list, /read <file>, /upload <file> <text>, /delete <file>, /info <file>\n")
    while True:
        try: data = conn.recv(4096)
        except: break
        if not data: break
        monitor.record_received(sock_id, len(data))
        text = data.decode('utf-8', errors='ignore').strip()
        if not text: continue
        cmd,*args = text.split(" ",1)
        role = client_meta[sock_id]['role']

        if cmd.lower()=="role":
            r=args[0].lower() if args else "user"
            if r=="admin" and len(args)>1 and args[1]==ADMIN_PASS: role='admin'
            client_meta[sock_id]['role']=role
            safe_send(conn, f"Assigned role: {role}\n".encode())
            continue

        response="Komandë e panjohur.\n"
        if cmd=="/list": response=list_files()
        elif cmd=="/read" and args: response=read_file(args[0])
        elif cmd=="/delete" and args and role=="admin": response=delete_file(args[0])
        elif cmd=="/info" and args: response=info_file(args[0])
        elif cmd=="/stats" and role=="admin": monitor.print_stats_to_console(); response="STATS shfaqur\n"

        safe_send(conn, response.encode())

    close_socket(sock_id)
    print(f"Klienti {addr} shkëput.")

def accept_loop():
    while True:
        try: conn, addr = server_socket.accept()
        except: continue
        with lock:
            if len(client_sockets)>=MAX_CLIENTS: safe_send(conn,b"Server full.\n"); conn.close(); continue
        print(f"New client {addr}")
        threading.Thread(target=handle_client,args=(conn,addr),daemon=True).start()

if __name__=="__main__":
    print("Server running...")
    accept_loop()
