import sys
import threading
import socket

stop_thread = False  # flag për të ndaluar thread-in

def receive_messages(sock):
    global stop_thread
    buffer = ""
    while not stop_thread:
        try:
            data = sock.recv(8192)
            if not data:
                break

            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                sys.stdout.write(f"\n{line}\n\nShkruaj komandë (/exit për dalje): ")
                sys.stdout.flush()
        except:
            break

def main():
    global stop_thread
    role = input("Zgjedh rolin tënd (admin/user): ").strip().lower()
    if role not in ["admin","user"]:
        role = "user"

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 5000))

    if role == "admin":
        client_socket.send(b"role admin adminpass\n")
    else:
        client_socket.send(b"role user\n")

    recv_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    recv_thread.start()

    allowed_user_commands = ["/read", "/list", "/search"]

    while True:
        try:
            command = input().strip()

            if command == "/exit":
                stop_thread = True
                client_socket.close()
                recv_thread.join()
                break

            # Kontrolli për user
            if role == "user":
                if not any(command.startswith(cmd) for cmd in allowed_user_commands):
                    print("Komanda nuk ekziston ose nuk ke autorizim për të. Vetëm /read, /list dhe /search janë të lejuara.")
                    continue

            # Dërgo komandën te serveri
            try:
                client_socket.sendall((command + "\n").encode())
            except:
                print("Lidhja me serverin është mbyllur.")
                stop_thread = True
                break

        except KeyboardInterrupt:
            # Ctrl+C si exit
            stop_thread = True
            client_socket.close()
            recv_thread.join()
            break
        except Exception as e:
            print(f"Gabim gjatë komunikimit: {e}")
            stop_thread = True
            client_socket.close()
            recv_thread.join()
            break

if __name__ == "__main__":
    main()
