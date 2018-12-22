import argparse
import socket
import ssl
import time
import math
from threading import Thread
import random
import string

from utils import *

PORT = 443

def get_header(host, path):
	'''
	function to get header information from a request
	:param host: server domain
	:param path: path of the source file
	:return: header as a dict, and length of header in bytes
	'''
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.connect((host, PORT))

	soc = ssl.wrap_socket(soc, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)

	request = 'HEAD '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\n\r\n' # request header
	soc.sendall(request.encode())

	res = soc.recv(1024)
	res = res.decode()
	lines = res.split('\r\n')

	header = {}
	for i in range(len(lines)-2): # -2 for CRLF
		if i == 0:
			header['response'] = ' '.join(lines[i].split()[1:]) # first line
			continue
		field = lines[i].split(': ')
		if len(field) == 2:
			header[field[0].strip().lower()] = field[1].strip()
	soc.close()
	return header, len(res)


def tcp_download(host, path, start, end, dest):
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.connect((host, PORT))

	soc = ssl.wrap_socket(soc, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)

	if end is not math.inf:
		request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\nRange: bytes='+ str(start) +'-'+ str(end) +'\r\n\r\n' # request header
	else:
		request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\n\r\n' # request header

	soc.sendall(request.encode())

	with open(dest, 'wb') as file_to_write:
		hdr_rcvd = False # indicator that header is received
		rcvd_lngth = 0 # received data
		while True:
			data = soc.recv(2048)
			if not data:
				break
			if not hdr_rcvd:
				data = data.split(b'\r\n\r\n')[1] # skip header
				hdr_rcvd = True
			else:
				data = data
			file_to_write.write(data)

			rcvd_lngth += len(data)
			
			if rcvd_lngth >= (end - start): break
	soc.close()

# global dictionary to launch download based on connection type
connections = {'TCP': tcp_download}


# MAIN
if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	#[-r] -n NUM_CONNECTIONS -i METRIC_INTERVAL -c CONNECTION_TYPE -f URL -o DESTINATION
	parser.add_argument("-r", "--resume", action='store_true', help="Whether to resume the existing download in progress")
	requiredArgs = parser.add_argument_group('required arguments')
	requiredArgs.add_argument("-n", "--num", required=True, help="Total number of simultaneous connections", type=int)
	requiredArgs.add_argument("-i", "--interval", required=True, help="Time interval in seconds between metric reporting", type=int)
	requiredArgs.add_argument("-c", "--connection", required=True, help="Type of connection: UDP or TCP")
	requiredArgs.add_argument("-s", "--src", required=True, help="Address pointing to the file location on the web")
	requiredArgs.add_argument("-o", "--dest", required=True, help="Address pointing to the location where the file is downloaded")

	# parse arguments and store in respective variables
	args = parser.parse_args()
	num_con = args.num # number of simulatenous connections

	# get source details from source web link and resolve to destination link
	host, path, filename = parse_links(args.src, args.dest)
	# print(host, path, filename)

	# using abbrevation convention
	connection_type = args.connection.upper()
	start_t = time.time()

	header, hlength = get_header(host, path)
	#print(header)
	# process header information
	if 'response' in header and header['response'].find('200') != -1:
		print('\nSuccessfully connected to', socket.gethostbyname(host))
	else:
		print('\nFailed! Server replied with error:', header['response'])
		exit(1)

	clength = math.inf
	if 'content-length' in header:
		clength = int(header['content-length'])
	else:
		print('\nServer did not return length of file. Using defaults: single connection')
		num_con = 1

	if not 'accept-ranges' in header:
		print('\nServer does not support ranges. Using defaults: single connection')
		num_con = 1

	print('\nDownloading',filename,'...\n')

	if num_con == 1: # avoid overheads
		connections[connection_type](host, path, 0, clength, filename)
		print(time.time() - start_t)
		exit(0)

	threads = [] # list of threads
	tmps = [] # list of intermediate files
	multiple = clength // num_con
	for i in range(num_con):
		print('Creating connection #', i+1)
		tmp_name = '.'+''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=15))

		start = i*multiple
		end = (i+1)*multiple-1
		if i == num_con - 1:
			end = clength

		threads.append( Thread(target=connections[connection_type], args=(host, path, start, end, tmp_name)) )
		threads[-1].start()
		tmps.append(tmp_name)

	for i in range(num_con):
		threads[i].join()

	print('\nDownload Completed!\n')
	print(time.time() - start_t, 'sec')

	print('\nCombining chunks...')
	join_chunks(tmps, filename)