import argparse
import socket
import os
from urllib.parse import urlparse

PORT = 80

def udp_download(host, filename, dest):
	soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	soc.connect((host, PORT))
	request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\n\r\n' # request header
	soc.sendall(request.encode())

	filename = path.split('/')[-1] # filname comes last
	if filename == '':
		filename = 'index.html'

	with open(os.path.join(dest, filename), 'w') as file_to_write:
		hdr_rcvd = False # indicator that header is received
		while True:
			soc.settimeout(100)
			data = soc.recv(1024)
			if not data:
				break
			if not hdr_rcvd:
				data = data.decode().split('\r\n\r\n')
				print(data[0])
				data = ''.join(data[1:])
				hdr_rcvd = True
			else:
				data = data.decode()
			file_to_write.write(data)
		file_to_write.close()
	soc.close()

def tcp_download(host, path, dest):
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.connect((host, PORT))
	request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\n\r\n' # request header
	soc.sendall(request.encode())

	filename = path.split('/')[-1] # filname comes last
	if filename == '':
		filename = 'index.html'

	with open(os.path.join(dest, filename), 'w') as file_to_write:
		hdr_rcvd = False # indicator that header is received
		while True:
			data = soc.recv(1024)
			if not data:
				break
			if not hdr_rcvd:
				data = data.decode().split('\r\n\r\n')
				print(data[0])
				data = ''.join(data[1:])
				hdr_rcvd = True
			else:
				data = data.decode()
			file_to_write.write(data)
		file_to_write.close()
	soc.close()

# global dictionary to launch download based on connection type
connections = {'UDP': udp_download, 'TCP': tcp_download}

if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	#[-r] -n NUM_CONNECTIONS -i METRIC_INTERVAL -c CONNECTION_TYPE -f URL -o DESTINATION
	parser.add_argument("-r", "--resume", action='store_true', help="Whether to resume the existing download in progress")
	requiredArgs = parser.add_argument_group('required arguments')
	requiredArgs.add_argument("-n", "--num", required=True, help="Total number of simultaneous connections", type=int)
	requiredArgs.add_argument("-i", "--interval", required=True, help="Time interval in seconds between metric reporting", type=int)
	requiredArgs.add_argument("-c", "--connection", required=True, help="Type of connection: UDP or TCP")
	requiredArgs.add_argument("-f", "--src", required=True, help="Address pointing to the file location on the web")
	requiredArgs.add_argument("-o", "--dest", required=True, help="Address pointing to the location where the file is downloaded")

	# parse arguments and store in respective variables
	args = parser.parse_args()

	# get source details from source web link
	url = urlparse(args.src)
	host = url.netloc
	path = url.path
	if url.scheme == '':
		host = url.path.split('/')[0] # if scheme is not present, domain comes before first slash '/'
	if path == '':
		path = '/' # request root i.e., index.html by convention

	# using abbrevation convention
	connection_type = args.connection.upper()
	
	connections[connection_type](host, path, args.dest)