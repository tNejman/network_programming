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

TYPE_STANDARD_ENCRYPTED = 1
TYPE_END_SESSION = 3
TYPE_SERVER_OK = 2
CONTENT_END_SESSION = "ENDSSION"
CONTENT_SERVER_OK = "SRVOK"

def send_encrypted_message(sock, K, session_prng, message_type, message_bytes):
    keystream_header = session_prng.randbytes(MESSAGE_HEADER_SIZE)
    encoded_message = message_bytes
    msg_size = len(encoded_message)
    keystream_content = session_prng.randbytes(msg_size)

    
    msg_type = message_type
    
    encrypted_message = bytes(a ^ b for a, b in zip(encoded_message, keystream_content))
    k_bytes = K.to_bytes((K.bit_length() + 7) // 8 or 1, byteorder='big')
            
    calculated_hmac = hmac.new(k_bytes, encrypted_message, hashlib.sha224).digest()
    msg_header = struct.pack('!28sIQ', calculated_hmac, msg_type, msg_size)
    encrypted_header = bytes(a ^ b for a, b in zip(msg_header, keystream_header))
    msg = encrypted_header + encrypted_message
    print(f'[Klient] Zakodowana wiadomość payload=\"{encoded_message}\" hmac={calculated_hmac} ')
    sock.sendall(msg)

def recive_encrypted_message(conn, session_prng, K, addr):
    encrypted_header = recv_exactly(conn, MESSAGE_HEADER_SIZE)
    if not encrypted_header:
        return True

    keystream_header = session_prng.randbytes(MESSAGE_HEADER_SIZE)
    decrypted_header = bytes(a ^ b for a, b in zip(encrypted_header, keystream_header))

    recv_hmac, msg_type, msg_size = struct.unpack('!28sIQ', decrypted_header)

    if msg_size > 0:
        encrypted_content = recv_exactly(conn, msg_size)
        if not encrypted_content:
            return False
        
        keystream_content = session_prng.randbytes(msg_size)
        decrypted_content = bytes(a ^ b for a, b in zip(encrypted_content, keystream_content))
    else:
        decrypted_content = b''
    
    payload_to_verify = encrypted_content
    k_bytes = K.to_bytes((K.bit_length() + 7) // 8 or 1, byteorder='big')
    
    calculated_hmac = hmac.new(k_bytes, payload_to_verify, hashlib.sha224).digest()

    print(f'[{addr}] Odebrano dekodowaną wiadomość calculated_hmac=\"{calculated_hmac}\" recv_hmac={recv_hmac} ')

    if hmac.compare_digest(calculated_hmac, recv_hmac):
        # Autoryzacja OK
        if msg_type == 3: # EndSession [cite: 60]
            print(f"[{addr}] Otrzymano EndSession. Zamykanie.")
            return False
        else:
            try:
                print(f"[{addr}] Wiadomość: {decrypted_content.decode('utf-8').rstrip(chr(0))}") # usuwamy null bytes

                send_encrypted_message(conn, K, session_prng, TYPE_SERVER_OK, msg_size.to_bytes(8, byteorder="big"))
                return True
            except BaseException as e:
                print(f"[{addr}] Exception occurred while decoding: {type(e).__name__}: {e}")
                print(f"[{addr}] Wiadomość binarna o rozmiarze {msg_size}")
                return True
    else:
        print(f"[{addr}] BŁĄD INTEGRALNOŚCI! Odrzucono wiadomość.")
        # W prawdziwym systemie tutaj zrywamy połączenie
        return False

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

        continue_communication = True
        while continue_communication:            
            continue_communication = recive_encrypted_message(conn, session_prng, K, addr)
            if not continue_communication:
                print("communication will be not continued")


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