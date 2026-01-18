import struct
import hashlib
import hmac
import sys
import secrets

MESSAGE_HMAC_SIZE = 28
MESSAGE_TYPE_SIZE = 4
MESSAGE_SIZE_SIZE = 8
MESSAGE_HEADER_SIZE = MESSAGE_HMAC_SIZE + MESSAGE_TYPE_SIZE + MESSAGE_SIZE_SIZE

TYPE_STANDARD_ENCRYPTED = 1
TYPE_END_SESSION = 3
TYPE_OK = 2

CONTENT_END_SESSION = "ENDSSION"

CLIENT_HELLO_BYTE_SIZE = 28
SERVER_HELLO_BYTE_SIZE = 12
CLIENT_HELLO_SIGNATURE = "HELO"
SEVER_HELLO_SIGNATURE = "EHLO"

MAX_RANDINT_EXCLUSIVE = 1_000_000

def get_derived_seed(K, suffix):
    raw = f"{K}_{suffix}".encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)

def recv_exactly(conn, bytes_to_receive_count: int):
    if bytes_to_receive_count == 0:
        raise RuntimeError("Tried receiving 0 bytes")
    data = b''
    while len(data) < bytes_to_receive_count:
        packet = conn.recv(bytes_to_receive_count - len(data))
        if not packet:
            raise RuntimeError("Connection lost; returned 0 bytes")
        data += packet
    return data

def send_encrypted_message(sock, K, prng_encoder, message_type, encoded_message):
    keystream_header = prng_encoder.randbytes(MESSAGE_HEADER_SIZE)
    msg_size = len(encoded_message)
    keystream_content = prng_encoder.randbytes(msg_size)
    
    encrypted_message = bytes(a ^ b for a, b in zip(encoded_message, keystream_content))
    k_bytes = K.to_bytes((K.bit_length() + 7) // 8 or 1, byteorder='big')
            
    calculated_hmac = hmac.new(k_bytes, encrypted_message, hashlib.sha224).digest()
    msg_header = struct.pack('!28sIQ', calculated_hmac, message_type, msg_size)
    encrypted_header = bytes(a ^ b for a, b in zip(msg_header, keystream_header))
    msg = encrypted_header + encrypted_message
    
    sock.sendall(msg)
    
def recive_encrypted_message(conn, prng_decoder, K, addr):
    try:
        encrypted_header = recv_exactly(conn, MESSAGE_HEADER_SIZE)
    except RuntimeError:
        return False
        
    if not encrypted_header:
        return False

    keystream_header = prng_decoder.randbytes(MESSAGE_HEADER_SIZE)
    decrypted_header = bytes(a ^ b for a, b in zip(encrypted_header, keystream_header))

    recv_hmac, msg_type, msg_size = struct.unpack('!28sIQ', decrypted_header)

    if msg_size > 0:
        encrypted_content = recv_exactly(conn, msg_size)
        if not encrypted_content:
            return False
        
        keystream_content = prng_decoder.randbytes(msg_size)
        decrypted_content = bytes(a ^ b for a, b in zip(encrypted_content, keystream_content))
    else:
        decrypted_content = b''
    
    k_bytes = K.to_bytes((K.bit_length() + 7) // 8 or 1, byteorder='big')    
    calculated_hmac = hmac.new(k_bytes, encrypted_content, hashlib.sha224).digest()

    if hmac.compare_digest(calculated_hmac, recv_hmac):
        if msg_type == TYPE_END_SESSION:
            print(f"\n[{addr}] Otrzymano ENDSSION. Zamykanie.")
            return False
        elif msg_type == TYPE_STANDARD_ENCRYPTED:
            try:
                msg_text = decrypted_content.decode('utf-8').rstrip(chr(0))
                print(f"\n[{addr}]: {msg_text}")
            except BaseException as e:
                print(f"\n[{addr}] Błąd dekodowania: {e}")
            finally:
                return True
        elif msg_type == TYPE_OK:
            print(f"[{addr}] Otrzymano potwierdzenie.")
            return True
    else:
        print(f"\n[{addr}] BŁĄD INTEGRALNOŚCI! Odrzucono wiadomość.")
        return False
    return True

def log(message):
    sys.stdout.write(f"\r{message}\n> ")
    sys.stdout.flush()
    
def generate_cryptographically_safe_randint() -> int:
    return secrets.randbelow(MAX_RANDINT_EXCLUSIVE)