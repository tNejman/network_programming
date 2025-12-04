import socket
import struct
import hashlib

HOST = "0.0.0.0"
PORT = 8888

PAYLOAD_SIZE = 100
PACKETS_NUM = 100
FILE_SIZE = PAYLOAD_SIZE * PACKETS_NUM

ACK_TEXT = "OK"
ACK_BYTES = ACK_TEXT.encode("ascii")

def process_packet(data):
    if len(data) != 4 + PAYLOAD_SIZE:
        print("Invalid packet length: ", len(data))
        return None
    number = struct.unpack(">i", data[:4])[0]
    payload = data[4:4+PAYLOAD_SIZE]
    if (number < 0 or number >= PACKETS_NUM):
        print("Incorrect file index: ", number)
        return None
    
    print("Packet recived #", number)
    return number, payload

def send_ok_response(sock, addr, packet_id):
    response = struct.pack(">i", packet_id) + ACK_BYTES
    sock.sendto(response, addr)

def reconstruct_file_and_verify(file_bytes):
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    print("SHA-256:", sha256_hash)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        print(f"UDP server listening on {HOST}:{PORT}")

        is_received = [False] * PACKETS_NUM
        file_bytes = bytearray(FILE_SIZE)
        while True:
            data, addr = s.recvfrom(4 + PAYLOAD_SIZE)
            if not data:
                continue

            result =  process_packet(data)
            if result is None:
                continue
            packet_id, payload = result
            start_i = PAYLOAD_SIZE*(packet_id)
            end_i = start_i + PAYLOAD_SIZE
            file_bytes[start_i:end_i] = payload
            is_received[packet_id] = True

            send_ok_response(s, addr, packet_id)

            if all(is_received):
                break
        
        reconstruct_file_and_verify(file_bytes)


if __name__ == "__main__":
    main()
