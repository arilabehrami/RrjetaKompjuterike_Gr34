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



def main():
    print("=== SISTEMI I KLIENTIT ===\n")
    print("Zgjedh rolin tënd:")
    print("1. Admin (qasje e plotë: /list, /read, /upload, /download, /delete, /info)")
    print("2. Përdorues i thjeshtë (vetëm /list, /read, /info)\n")

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

        # Kontrollo privilegjet e user-it
        if role == "user":
            allowed = ["/list", "/read", "/info"]
            if not any(command.startswith(cmd) for cmd in allowed):
                print("Nuk ke leje për këtë komandë. Lejohen vetëm: /list, /read <file>, /info <file>\n")
                continue

        try:
            # Admini dërgon menjëherë
            if role == "admin":
                client_socket.send(command.encode())
            else:
                # Përdoruesi pret pak (për të simuluar prioritet më të ulët)
                time.sleep(0.4)
                client_socket.send(command.encode())

            # Merr përgjigjen
            response = client_socket.recv(8192).decode()
            print("\n Përgjigja nga serveri:")
            print("---------------------------------------")
            print(response)
            print("---------------------------------------")

            # Serveri mbyll lidhjen pas komandës, prandaj rilidhemi
            client_socket.close()
            client_socket = connect_to_server()
            if not client_socket:
                break

        except Exception as e:
            print(f"Gabim gjatë komunikimit: {e}")
            client_socket.close()
            break

  