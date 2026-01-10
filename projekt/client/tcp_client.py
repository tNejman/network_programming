import socket
import struct
import random
import hashlib
import hmac

MESSAGE_HMAC_SIZE = 28
MESSAGE_TYPE_SIZE = 4
MESSAGE_SIZE_SIZE = 8
MESSAGE_HEADER_SIZE = MESSAGE_HMAC_SIZE + MESSAGE_TYPE_SIZE + MESSAGE_SIZE_SIZE

TYPE_STANDARD_ENCRYPTED = 1
TYPE_END_SESSION = 3
TYPE_SERVER_OK = 2
CONTENT_END_SESSION = "ENDSSION"

def recv_exactly(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def send_encrypted_message(sock, K, session_prng, message_type, message_text):
    keystream_header = session_prng.randbytes(MESSAGE_HEADER_SIZE)
    encoded_message = message_text.encode()
    msg_size = len(encoded_message)
    keystream_content = session_prng.randbytes(msg_size)

    
    msg_type = message_type
    
    encrypted_message = bytes(a ^ b for a, b in zip(encoded_message, keystream_content))
    k_bytes = K.to_bytes((K.bit_length() + 7) // 8 or 1, byteorder='big')
            
    calculated_hmac = hmac.new(k_bytes, encrypted_message, hashlib.sha224).digest()
    msg_header = struct.pack('!28sIQ', calculated_hmac, msg_type, msg_size)
    encrypted_header = bytes(a ^ b for a, b in zip(msg_header, keystream_header))
    msg = encrypted_header + encrypted_message
    print(f'[Klient] Zakodowana wiadomość text=\"{message_text}\" hmac={calculated_hmac} ')
    sock.sendall(msg)

def check_for_server_ok_message(conn, K, session_prng, expected_length):
    encrypted_header = recv_exactly(conn, MESSAGE_HEADER_SIZE)
    if not encrypted_header:
        return False

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

    if hmac.compare_digest(calculated_hmac, recv_hmac):
        # Autoryzacja OK
        recv_message_length = struct.unpack('!Q', decrypted_content)[0]
        if msg_type == TYPE_SERVER_OK and expected_length == recv_message_length:
            print(f"[Klient] Otrzymano potwierdzenie otrzymania wiadomości")
            return True
        else:
            return False
    else:
        return False

def simple_tcp_client():
    host = '127.0.0.1'
    port = 5555

    p = 23
    g = 5
    a_priv = 6
    A = pow(g, a_priv, p)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"[Klient] Połączono z {host}:{port}")

        msg_string = b"HELO"
        packet = struct.pack('!4sQQQ', msg_string, p, g, A)

        sock.sendall(packet)
        print(f"[Klient] Wysłano dane: HELO, p={p}, g={g}, A={A}")

        expected_length = 12
        response_data = sock.recv(expected_length)

        if len(response_data) < expected_length:
            print("[Błąd] Otrzymano niekompletną odpowiedź.")
            return

        resp_string, B = struct.unpack('!4sQ', response_data)

        decoded_string = resp_string.decode('utf-8', errors='ignore')

        print(f"[Klient] Odebrano: String='{decoded_string}', B={B}")
        K = pow(B, a_priv, p)
        print(f"[Klient] Wyliczono wspólny klucz: K='{K}'")
        
        session_prng = random.Random(K)

        message_text = input('Podaj wiadomość:')
        message_text_length = len(message_text)
        
        send_encrypted_message(sock, K, session_prng, TYPE_STANDARD_ENCRYPTED, message_text)

        while not check_for_server_ok_message(sock, K, session_prng, message_text_length):
            continue

        send_encrypted_message(sock, K, session_prng, TYPE_END_SESSION, CONTENT_END_SESSION)
        
        

    except ConnectionRefusedError:
        print("[Błąd] Nie można połączyć się z serwerem. Upewnij się, że serwer działa.")
    except Exception as e:
        print(f"[Błąd] Wystąpił wyjątek: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    simple_tcp_client()