import socket
import struct
import random

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
        
        seesion_prng = random.Random(K)
        
        

    except ConnectionRefusedError:
        print("[Błąd] Nie można połączyć się z serwerem. Upewnij się, że serwer działa.")
    except Exception as e:
        print(f"[Błąd] Wystąpił wyjątek: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    simple_tcp_client()