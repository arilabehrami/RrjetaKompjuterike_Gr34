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
        return client_socket
    except Exception as e:
        print(f" Nuk u arrit lidhja me serverin: {e}")
        return None

def main():
    print("=== SISTEMI I KLIENTIT ===\n")
    print("Zgjedh rolin tënd:")
    print("1. Admin")
    print("2. Përdorues i thjeshtë\n")

    choice = input("Zgjedh (1 ose 2): ").strip()
    if choice == "1":
        role = "admin"
        print("\n Je lidhur si ADMIN.\n")
    else:
        role = "user"
        print("\n Je lidhur si PËRDORUES i thjeshtë.\n")

    client_socket = connect_to_server()
    if not client_socket:
        return

    while True:
        command = input("\nShkruaj komandë (/exit për dalje): ").strip()

        if command == "/exit":
            print("Lidhja u mbyll nga klienti.")
            client_socket.close()
            break

        if role == "user":
            allowed = ["/list", "/read", "/info"]
            if not any(command.startswith(cmd) for cmd in allowed):
                print("Nuk ke leje për këtë komandë.\n")
                continue

        try:
            if role == "admin":
                client_socket.send(command.encode())
            else:
                time.sleep(0.4)
                client_socket.send(command.encode())

            response = client_socket.recv(8192).decode()
            print("\n Përgjigja nga serveri:")
            print("---------------------------------------")
            print(response)
            print("---------------------------------------")

            client_socket.close()
            client_socket = connect_to_server()
            if not client_socket:
                break
                
        except Exception as e:
            print(f"Gabim gjatë komunikimit: {e}")
            try:
                client_socket.close()
            except:
                pass
            break



if __name__ == "__main__":
    main()
