import socket
import struct
import threading
import random
import hashlib
import hmac
import argparse

CLIENT_HELLO_BYTE_SIZE = 28
SERVER_HELLO_BYTE_SIZE = 12
CLIENT_HELLO_SIGNATURE = "HELO"
SEVER_HELLO_SIGNATURE = "EHLO"

MESSAGE_HMAC_SIZE = 28
MESSAGE_TYPE_SIZE = 4
MESSAGE_SIZE_SIZE = 8
MESSAGE_HEADER_SIZE = MESSAGE_HMAC_SIZE + MESSAGE_TYPE_SIZE + MESSAGE_SIZE_SIZE

def recv_exactly(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_client(conn, addr):
    print(f"[NOWY] Połączono z {addr}")
    session_prng = None 

    try:
        header_data = recv_exactly(conn, CLIENT_HELLO_BYTE_SIZE)
        if not header_data:
            return

        sig, p, g, A = struct.unpack('!4sQQQ', header_data)
        
        if sig != CLIENT_HELLO_SIGNATURE.encode():
            print(f"[BLAD] Nieprawidłowa sygnatura od {addr}")
            return

        print(f"[{addr}] Otrzymano p={p}, g={g}, A={A}")

        # b_priv = random.randint(2, 100) 
        b_priv = 15
        B = pow(g, b_priv, p)

        K = pow(A, b_priv, p)
        print(f"[{addr}] Wyliczono wspólny klucz K={K}")
        session_prng = random.Random(K)

        response = struct.pack('!4sQ', SEVER_HELLO_SIGNATURE.encode(), B)
        conn.sendall(response)

        while True:            
            encrypted_header = recv_exactly(conn, MESSAGE_HEADER_SIZE)
            if not encrypted_header:
                break

            keystream_header = session_prng.randbytes(MESSAGE_HEADER_SIZE)
            decrypted_header = bytes(a ^ b for a, b in zip(encrypted_header, keystream_header))

            recv_hmac, msg_type, msg_size = struct.unpack('!28sIQ', decrypted_header)

            if msg_size > 0:
                encrypted_content = recv_exactly(conn, msg_size)
                if not encrypted_content:
                    break
                
                keystream_content = session_prng.randbytes(msg_size)
                decrypted_content = bytes(a ^ b for a, b in zip(encrypted_content, keystream_content))
            else:
                decrypted_content = b''
            
            payload_to_verify = struct.pack('!IQ', msg_type, msg_size) + decrypted_content

            k_bytes = K.to_bytes((K.bit_length() + 7) // 8 or 1, byteorder='big')
            
            calculated_hmac = hmac.new(k_bytes, payload_to_verify, hashlib.sha224).digest()

            if hmac.compare_digest(calculated_hmac, recv_hmac):
                # Autoryzacja OK
                if msg_type == 3: # EndSession [cite: 60]
                    print(f"[{addr}] Otrzymano EndSession. Zamykanie.")
                    break
                else:
                    try:
                        print(f"[{addr}] Wiadomość: {decrypted_content.decode('utf-8').rstrip(chr(0))}") # usuwamy null bytes
                    except:
                        print(f"[{addr}] Wiadomość binarna o rozmiarze {msg_size}")
            else:
                print(f"[{addr}] BŁĄD INTEGRALNOŚCI! Odrzucono wiadomość.")
                # W prawdziwym systemie tutaj zrywamy połączenie
                break

    except Exception as e:
        print(f"[{addr}] Błąd obsługi: {e}")
    finally:
        conn.close()
        print(f"[ROZLACZONO] {addr}")

def start_server(host, port, max_clients):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    
    server.listen(5) 
    print(f"[START] Serwer nasłuchuje na {host}:{port}")
    print(f"[LIMIT] Maksymalna liczba aktywnych klientów: {max_clients}")

    while True:
        conn, addr = server.accept()
        
        active_connections = threading.active_count() - 1
        
        if active_connections >= max_clients:
            print(f"[ODRZUCONO] {addr} - Serwer pełny ({active_connections}/{max_clients})")
            try:
                conn.send(b"Serwer pelny. Sprobuj pozniej.\n")
                conn.close()
            except:
                pass
            continue

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[INFO] Aktywne połączenia: {threading.active_count() - 1}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Server')
    parser.add_argument('max_clients', type=int, help='Maksymalna liczba jednoczesnych klientów')
    args = parser.parse_args()

    try:
        start_server('127.0.0.1', 5555, args.max_clients)
    except KeyboardInterrupt:
        print("KeyboardInterrupt: terminating session")