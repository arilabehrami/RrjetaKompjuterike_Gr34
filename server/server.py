import os
import socket
import threading
import time
from monitoring.monitor import Monitor

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


IP = "127.0.0.1"
PORT = 5000
MAX_CLIENTS = 4

FILES_DIR = "server_files"
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

ADMIN_PASS = "adminpass"
STATS_FILE = 'monitoring/server_stats.txt'
UPDATE_INTERVAL = 5
TIMEOUT_SECONDS = 60


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()
print(f"Serveri është duke dëgjuar në {IP}:{PORT}")

client_sockets = {}
client_lock = threading.Lock()

client_meta = {}
meta_lock = threading.Lock()

active_addrs = []

def list_files():
    files = os.listdir(FILES_DIR)
    if not files:
        return "Nuk ka asnjë file në server.\n"
    return "\n".join(files) + "\n"

def read_file(filename):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return "File nuk ekziston.\n"
    with open(path, "rb") as f:
        data = f.read()
    try:
        return data.decode('utf-8') + "\n"
    except Exception:
        return "[BINARY FILE] Përmbajtja nuk mund të shfaqet si tekst.\n"

def upload_file_from_bytes(filename, content_bytes):
    path = os.path.join(FILES_DIR, filename)
    with open(path, "wb") as f:
        f.write(content_bytes)
    return f"File '{filename}' u ngarkua me sukses.\n"

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
    mtime = time.ctime(os.path.getmtime(path))
    ctime = time.ctime(os.path.getctime(path))
    return f"Emri: {filename}\nMadhësia: {size} bytes\nKrijimi: {ctime}\nModifikimi: {mtime}\n"

def download_file_bytes(filename):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return None, "File nuk ekziston.\n"
    with open(path, "rb") as f:
        return f.read(), None


def close_socket_by_id(sock_id):
    """Thirret nga Monitor kur klienti timeout -> mbyll socketin."""
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
            with meta_lock:
                client_meta.pop(sock_id, None)
            del client_sockets[sock_id]
            print(f"[Monitor callback] Socket me id {sock_id} u mbyll për shkak timeout.")


monitor = Monitor(stats_file_path=STATS_FILE, update_interval=UPDATE_INTERVAL, timeout_seconds=TIMEOUT_SECONDS)
monitor.start(close_callback=close_socket_by_id)
admin_thread = threading.Thread(target=monitor.admin_console_loop, daemon=True)
admin_thread.start()


def safe_send(sock, data_bytes):
    try:
        sock.sendall(data_bytes)
    except Exception:
        try:
            sock.close()
        except Exception:
            pass


def handle_client(conn, addr):
    sock_id = id(conn)
    with client_lock:
        client_sockets[sock_id] = conn
    with meta_lock:
        client_meta[sock_id] = {'addr': addr, 'role': 'unknown', 'last_cmd_time': time.time()}
    monitor.register(sock_id, addr)
    with client_lock:
        if addr not in active_addrs:
            active_addrs.append(addr)

    try:
        welcome = (
            "Përshëndetje! Je lidhur me serverin.\n"
            "Për t'u identifikuar dërgo:\n"
            "  ROLE user\n"
            "ose\n"
            "  ROLE admin <password>\n"
            "Komandat: /list, /read <file>, /upload <file> <size?>, /download <file>, /delete <file>, /info <file>\n"
            "Admin mund të përdorë /stats (shfaq stats në server) dhe ka privilegje të plota.\n"
        )
        safe_send(conn, welcome.encode('utf-8'))

        while True:
            try:
                data = conn.recv(4096)
            except ConnectionResetError:
                break
            if not data:
                break

            try:
                monitor.record_received(sock_id, len(data))
            except Exception:
                pass

            try:
                text = data.decode('utf-8', errors='ignore').strip()
            except Exception:
                text = ''
            if not text:
                continue

            with meta_lock:
                client_meta[sock_id]['last_cmd_time'] = time.time()

            print(f"[{addr}] -> {text}")
            parts = text.split(" ", 2)
            cmd = parts[0].lower()

            if cmd == "role":
                if len(parts) >= 2:
                    role_candidate = parts[1].lower()
                    if role_candidate == "admin":
                        given = parts[2].strip() if len(parts) > 2 else ""
                        if given == ADMIN_PASS:
                            with meta_lock:
                                client_meta[sock_id]['role'] = 'admin'
                            safe_send(conn, "Je autorizuar si ADMIN.\n".encode('utf-8'))
                        else:
                            safe_send(conn, "Fjalëkalim i gabuar. Do të jesh user (vetëm read).\n".encode('utf-8'))
                            with meta_lock:
                                client_meta[sock_id]['role'] = 'user'
                    else:
                        with meta_lock:
                            client_meta[sock_id]['role'] = 'user'
                        safe_send(conn, "Je vendosur si USER.\n".encode('utf-8'))
                else:
                    safe_send(conn, "Sintaksa: ROLE user  ose  ROLE admin <password>\n".encode('utf-8'))
                continue

            with meta_lock:
                role = client_meta[sock_id].get('role', 'user')

            if role != 'admin':
                time.sleep(0.05)

            response = "Komandë e panjohur ose parametra të munguar.\n"

            if cmd == "/list":
                response = list_files()
            elif cmd == "/read" and len(parts) > 1:
                response = read_file(parts[1].strip())
            elif cmd == "/upload" and len(parts) > 1:
                sub = parts[1].strip()
                if " " in sub and len(parts) == 2:
                    fn = sub.split()[0]
                    response = "Sintaksë e gabuar për /upload.\n"
                else:
                    if len(parts) > 2 and parts[2].strip().isdigit():
                        filename = parts[1].strip()
                        size = int(parts[2].strip())
                        safe_send(conn, f"PREPARE {size}\n".encode('utf-8'))
                        received = b''
                        remaining = size
                        while remaining > 0:
                            chunk = conn.recv(min(4096, remaining))
                            if not chunk:
                                break
                            received += chunk
                            remaining -= len(chunk)
                            try:
                                monitor.record_received(sock_id, len(chunk))
                            except Exception:
                                pass
                        response = upload_file_from_bytes(filename, received)
                    elif len(parts) > 2:
                        filename = parts[1].strip()
                        content = parts[2]
                        response = upload_file_from_bytes(filename, content.encode('utf-8'))
                    else:
                        response = "Sintaksë për /upload: /upload <filename> <size>  ose  /upload <filename> <text>\n"
            elif cmd == "/download" and len(parts) > 1:
                filename = parts[1].strip()
                data_bytes, err = download_file_bytes(filename)
                if err:
                    response = err
                    safe_send(conn, response.encode('utf-8'))
                else:
                    header = f"FILESIZE {len(data_bytes)}\n"
                    safe_send(conn, header.encode('utf-8'))
                    try:
                        safe_send(conn, data_bytes)
                    except Exception:
                        pass
                    response = ""
            elif cmd == "/delete" and len(parts) > 1:
                if role != 'admin':
                    response = "Nuk ke privilegje për të fshirë file.\n"
                else:
                    response = delete_file(parts[1].strip())
            elif cmd == "/info" and len(parts) > 1:
                response = info_file(parts[1].strip())
            elif cmd == "/stats":
                if role == 'admin':
                    monitor.print_stats_to_console()
                    response = "STATS u shfaqën në server (konsolë).\n"
                else:
                    response = "Nuk ke privilegje për të parë STATS.\n"
            else:
                response = "Komandë e panjohur ose parametra të munguar.\n"

            if response:
                safe_send(conn, response.encode('utf-8'))

    except Exception as e:
        print("Gabim në handle_client:", e)
    finally:
        try:
            monitor.unregister(sock_id)
        except Exception:
            pass
        with client_lock:
            client_sockets.pop(sock_id, None)
        with meta_lock:
            client_meta.pop(sock_id, None)
        try:
            if addr in active_addrs:
                active_addrs.remove(addr)
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        print(f"Klienti {addr} u shkëput.")


def accept_loop():
    while True:
        try:
            conn, addr = server_socket.accept()
        except Exception as e:
            print("Gabim në accept():", e)
            continue

        print(f"Klient i ri nga: {addr}")

        with client_lock:
            if len(client_sockets) >= MAX_CLIENTS:
                print("Serveri është plot. Lidhja u refuzua.")
                try:
                    conn.sendall("Serveri është plot. Provo më vonë.\n".encode('utf-8'))
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                continue

        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    print("Server running. Prisni lidhje...")
    accept_loop()
