import socket
import struct
import threading
import random
import hashlib
import hmac
import argparse
import sys
import os

from proj_lib import *

active_clients_map = {}
map_lock = threading.Lock()

def handle_client(conn, addr):
    log(f"[NOWY] Połączono z {addr}")
    prng_decoder = None
    prng_encoder = None
    K = None

    try:
        header_data = recv_exactly(conn, CLIENT_HELLO_BYTE_SIZE)
        if not header_data:
            return

        sig, p, g, A = struct.unpack('!4sQQQ', header_data)
        
        if sig != CLIENT_HELLO_SIGNATURE.encode():
            log(f"[BLAD] Nieprawidłowa sygnatura od {addr}")
            return

        b_priv = generate_cryptographically_safe_randint()
        B = pow(g, b_priv, p)
        K = pow(A, b_priv, p)
        
        seed_enc = get_derived_seed(K, "S2C")
        seed_dec = get_derived_seed(K, "C2S")
        
        prng_encoder = random.Random(seed_enc)
        prng_decoder = random.Random(seed_dec)

        with map_lock:
            active_clients_map[addr] = {
                'conn': conn,
                'prng_enc': prng_encoder,
                'K': K
            }

        response = struct.pack('!4sQ', SEVER_HELLO_SIGNATURE.encode(), B)
        conn.sendall(response)
        log(f"[{addr}] Handshake OK. Klucz ustalony.")

        continue_communication = True
        while continue_communication:
            continue_communication = recive_encrypted_message(conn, prng_decoder, K, addr)

    except RuntimeError:
        pass
    except Exception as e:
        if "Bad file descriptor" not in str(e) and "closed" not in str(e):
            log(f"[{addr}] Błąd obsługi: {e}")
    finally:
        with map_lock:
            if addr in active_clients_map:
                del active_clients_map[addr]
        conn.close()
        log(f"[ROZLACZONO] {addr}")

def admin_console():
    """Wątek do wysyłania wiadomości z serwera do klientów"""
    
    def log_help():
        log("--- Konsola Administratora ---")
        log("Format: <ID> <Wiadomość>")
        log("Wpisz 'list', aby zobaczyć klientów.")
        log("Wpisz 'exit', aby zakończyć wszystkie sesje i zakończyć program.")
        log("Wpisz 'help', aby ponownie wyświetlić tę listę możliwych operacji.")
    
    log_help()
    while True:
        try:
            command = input()
            if not command: continue
            
            if command.strip() == "help":
                log_help()
                continue
            
            if command.strip() == "exit":
                with map_lock:
                    for client_data in active_clients_map.values():
                        try:
                            send_encrypted_message(
                                client_data['conn'],
                                client_data['K'],
                                client_data['prng_enc'],
                                TYPE_END_SESSION,
                                CONTENT_END_SESSION.encode()
                            )
                        except Exception as e:
                            log(f"Błąd przy rozłączaniu klienta: {e}")
                            
                    log("Ended all sessions")
                    os._exit(0)
            
            if command.strip() == "list":
                if len(active_clients_map) == 0:
                    log("Brak aktywnych klientów")
                    continue
                with map_lock:
                    log(f"Aktywni klienci:")
                    for idx, addr in enumerate(active_clients_map.keys()):
                        log(f"[{idx}] {addr}")
                continue
            

            parts = command.split(' ', 1)
            if len(parts) < 2:
                log("Błędny format. Użyj: <ID_z_listy> <Wiadomość>")
                continue
            
            try:
                target_idx = int(parts[0])
                msg_content = parts[1]
            except ValueError:
                log("ID musi być liczbą.")
                continue

            target_addr = None
            client_data = None
            
            with map_lock:
                clients_list = list(active_clients_map.keys())
                if 0 <= target_idx < len(clients_list):
                    target_addr = clients_list[target_idx]
                    client_data = active_clients_map[target_addr]
            
            if client_data:
                if msg_content == CONTENT_END_SESSION:
                    try:
                        send_encrypted_message(
                            client_data['conn'], 
                            client_data['K'], 
                            client_data['prng_enc'], 
                            TYPE_END_SESSION, 
                            msg_content.encode()
                        )
                    except Exception as e:
                        log(f"Błąd wysyłania ENDSSION do {target_addr}: {e}")

                    with map_lock:
                        try:
                            client_data['conn'].close()
                        except Exception:
                            pass
                        if target_addr in active_clients_map:
                            del active_clients_map[target_addr]
                    log(f"[Serwer -> {target_addr}]: Wysłano ENDSSION. Zakończono połączenie.")
                else:
                    try:
                        send_encrypted_message(
                            client_data['conn'], 
                            client_data['K'], 
                            client_data['prng_enc'], 
                            TYPE_STANDARD_ENCRYPTED, 
                            msg_content.encode()
                        )
                    except Exception as e:
                        log(f"Błąd wysyłania wiadomości do {target_addr}")
                    log(f"[Serwer -> {target_addr}]: Wysłano.")
            else:
                log("Klient nie istnieje.")

        except EOFError:
            break
        except Exception as e:
            log(f"Błąd konsoli: {e}")

def start_server(host, port, max_clients):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((host, port))
    except PermissionError:
        log(f"[Błąd] brak uprawnień do portu {port}")
        return
    
    server.listen(5) 
    log(f"[START] Serwer nasłuchuje na {host}:{port}")

    admin_thread = threading.Thread(target=admin_console)
    admin_thread.daemon = True
    admin_thread.start()

    try:
        while True:
            conn, addr = server.accept()
            
            if threading.active_count() - 2 >= max_clients:
                log(f"[ODRZUCONO] {addr} - Serwer pełny")
                conn.close()
                continue

            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        log("Zamykanie serwera...")
    finally:
        server.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Server')
    parser.add_argument('max_clients', type=int, help='Maksymalna liczba jednoczesnych klientów')
    args = parser.parse_args()

    start_server('0.0.0.0', 5000, args.max_clients)