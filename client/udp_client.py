import socket
import sys
import io
import numpy as np
from typing import Tuple
import time
import matplotlib.pyplot as plt
import random as rand
from math import log2

MAX_DATAGRAM_SIZE = 2 ** 1024
POSSIBLE_SYMBOLS = ['R','E','G','G', 'I', 'N']

def send_data(host: str, port: int, datagram_size: int) -> Tuple[bool, float]:
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
		s.connect((host, port))
		binary_stream = io.BytesIO()
		for _ in range(datagram_size):
			letter_to_be_written = POSSIBLE_SYMBOLS[rand.randint(0, len(POSSIBLE_SYMBOLS)-1)]
			binary_stream.write(letter_to_be_written.encode('ascii'))
		binary_stream.seek(0)
		stream_data = binary_stream.read()
		print("Sending buffer size= ", datagram_size)

		start_time = time.perf_counter()
		data = 0
		try:
			s.sendall(stream_data)
			data = s.recv(5)
		except Exception as e:
			print(e)
			time.sleep(0.05)
			return (False, -1)
		end_time = time.perf_counter()
		elapsed_time = end_time - start_time
	
		data_str = data.decode('ascii')
  
		if data_str == "OK":
			print('Received', data_str)
			s.close()
			return (True, elapsed_time)
		elif data_str == "ERROR":
			print('Received', data_str)
			s.close()
			return (False, elapsed_time)
		else:
			raise Exception("Unknown server reponse")

def find_max_datagram_size(host: str, port: int, initial_size: int = 2) -> Tuple[int, np.ndarray, np.ndarray]:
	lower_bound = 0
	test_size = initial_size
	datagram_sizes: np.ndarray = np.array([])
	times_measured: np.ndarray = np.array([])
 
	while test_size <= MAX_DATAGRAM_SIZE:	
		print(f"Testing doubling size: {test_size} bytes")	
		print(f"Interation: {int(log2(test_size))}")
  
		is_response_ok, elapsed_time = send_data(host, port, test_size)
		
		if is_response_ok:
			times_measured = np.append(times_measured, elapsed_time)
			datagram_sizes = np.append(datagram_sizes, test_size)
			lower_bound = test_size
			test_size *= 2
		else:
			break

	upper_bound = min(lower_bound*2, MAX_DATAGRAM_SIZE)
 
	if upper_bound == lower_bound:
		return (lower_bound, datagram_sizes, times_measured)

	while lower_bound < upper_bound:
		midpoint = (upper_bound + lower_bound) // 2
	
		is_response_ok, elapsed_time = send_data(host, port, midpoint)
	
		if is_response_ok:
			times_measured = np.append(times_measured, elapsed_time)
			datagram_sizes = np.append(datagram_sizes, test_size)
			lower_bound = midpoint
		else:
			upper_bound = midpoint - 1

	send_data(host, port, lower_bound)
	return (lower_bound, datagram_sizes, times_measured)

def main():
	if len(sys.argv) < 2: 
		print("no HOST, using localhost")
		print("no port, using 8888")
		host = '127.0.0.1'
		port=8888
	elif len(sys.argv) < 3:
		print("no port, using 8888")
		host = sys.argv[1]
		port=8888
	else:
		host = sys.argv[1]
		port = int( sys.argv[2] )

	print("Will send to ", host, ":", port)

	max_datagram_size, datagram_sizes, times_measured = find_max_datagram_size(host, port, 2)
	print(f"Max datagram size is: {max_datagram_size}")

	if (len(datagram_sizes) != len(times_measured)):
		raise Exception(f"Datagram sizes is of size: {len(datagram_sizes)} but times measured is of size {len(times_measured)}")
	plt.plot(datagram_sizes, times_measured)
	plt.xlabel("datagram size")
	plt.ylabel("time measured")
	plt.savefig("/images_saved/datagram_size_vs_time_measured.png")

	print('Client finished.')
 
if __name__ == "__main__":
    main()
