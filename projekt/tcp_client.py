import socket
import struct
import random
import hashlib
import hmac
import threading
import sys

from proj_lib import *

running = True

def receive_loop(sock, prng_decoder, K):
    """Wątek nasłuchujący wiadomości od serwera"""
    global running
    addr = "SERWER"
    while running:
        try:
            if not recive_encrypted_message(sock, prng_decoder, K, addr):
                print("\n[Info] Serwer zamknął połączenie lub błąd integralności.")
                running = False
                break
        except Exception as e:
            if running:
                print(f"\n[Błąd Odbioru]: {e}")
            break

def simple_tcp_client():
    global running
    host = '127.0.0.1'
    port = 5555

    p = 23
    g = 5
    a_priv = 6
    A = pow(g, a_priv, p)

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"[Klient] Połączono z {host}:{port}")

        packet = struct.pack('!4sQQQ', CLIENT_HELLO_SIGNATURE.encode(), p, g, A)
        sock.sendall(packet)

        expected_length = SERVER_HELLO_BYTE_SIZE
        response_data = sock.recv(expected_length)
        if len(response_data) < expected_length:
            print("[Błąd] Niekompletny handshake")
            return

        resp_string, B = struct.unpack('!4sQ', response_data)
        K = pow(B, a_priv, p)
        print(f"[Klient] Wspólny klucz K={K}")
        
        seed_enc = get_derived_seed(K, "C2S")
        seed_dec = get_derived_seed(K, "S2C")
        
        prng_encoder = random.Random(seed_enc)
        prng_decoder = random.Random(seed_dec)

        recv_thread = threading.Thread(target=receive_loop, args=(sock, prng_decoder, K))
        recv_thread.daemon = True
        recv_thread.start()

        print("--- Rozpoczęto czat (wpisz ENDSSION aby wyjść) ---")

        while running:
            try:
                message_text = input()
                if not running: break

                if message_text == CONTENT_END_SESSION:
                    send_encrypted_message(sock, K, prng_encoder, TYPE_END_SESSION, CONTENT_END_SESSION.encode()) 
                    running = False
                    break
                else:
                    send_encrypted_message(sock, K, prng_encoder, TYPE_STANDARD_ENCRYPTED, message_text.encode())
            except EOFError:
                break

    except ConnectionRefusedError:
        print("[Błąd] Nie można połączyć się z serwerem.")
    except Exception as e:
        print(f"[Błąd] Wyjątek: {e}")
    finally:
        running = False
        if sock:
            sock.close()
        print("[Klient] Zakończono.")

if __name__ == '__main__':
    simple_tcp_client()