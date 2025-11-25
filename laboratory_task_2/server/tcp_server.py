import socket

HOST = "0.0.0.0"
PORT = 8888

def calculate(a, op, b):
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        if b == 0:
            return "ERROR: division by zero"
        return a / b
    elif op == "^":
        return a ** b
    else:
        return "ERROR: unknown operator"

def handle_client(conn, addr):
    print(f"Connected with {addr}")
    try:
        while True:
            data1 = conn.recv(1024)
            if not data1:
                print(f"Client {addr} closed connection (first packet).")
                break

            op_data = conn.recv(1)
            if not op_data:
                print(f"Client {addr} closed connection (operator).")
                break

            data2 = conn.recv(1024)
            if not data2:
                print(f"Client {addr} closed connection (third packet).")
                break

            try:
                a_str = data1.decode("utf-8").strip()
                op = op_data.decode("utf-8").strip()
                b_str = data2.decode("utf-8").strip()

                a = float(a_str)
                b = float(b_str)
            except Exception as e:
                result = f"ERROR: invalid data ({e})"
                conn.sendall(result.encode("utf-8"))
                continue

            result = calculate(a, op, b)

            if isinstance(result, (int, float)):
                result_str = str(result)
            else:
                result_str = result

            conn.sendall(result_str.encode("utf-8"))
            print(f"{addr}: {a_str} {op} {b_str} = {result_str}")
    finally:
        conn.close()
        print(f"Connection with {addr} closed.")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    main()
