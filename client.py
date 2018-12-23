import argparse
import socket
import ssl
import time
from threading import Thread, Timer
import random
import string

from utils import *

PORT = 443

def get_header(host, path):
	'''
	function to get header information from a request
	:param host: server domain
	:param path: path of the source file
	:return: header as a dict
	'''
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.connect((host, 443))

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
	return header


def udp_download(host, path, start, end, dest, resume, id):
	'''
	function to download data in a file using UDP
	:param host: server domain
	:param path: path of the source file
	:param start: starting data byte
	:param ending: starting data byte
	:param dest: output file name
	:param resume: boolean flag indicating if user has requested resume
	:param id: connection number
	'''
	if start >= end:
		return
	soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	soc.connect((host, PORT))

	if end is not -1:
		request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\nRange: bytes='+ str(start) +'-'+ str(end) +'\r\n\r\n' # request header
	else:
		request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\n\r\n' # request header

	soc.sendall(request.encode())

	if resume:
		file_to_write = open(dest, 'ab')
	else:
		file_to_write = open(dest, 'wb')
	hdr_rcvd = False # indicator that header is received
	rcvd_lngth = 0 # received data
	while True:
		data = soc.recv(1400)
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


def tcp_download(host, path, start, end, dest, resume, id):
	'''
	function to download data in a file using TCP
	:param host: server domain
	:param path: path of the source file
	:param start: starting data byte
	:param ending: starting data byte
	:param dest: output file name
	:param resume: boolean flag indicating if user has requested resume
	:param id: connection number
	'''
	if start >= end:
		return
	total[id] = end-start+1
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.connect((host, PORT))

	soc = ssl.wrap_socket(soc, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)

	if end is not -1:
		request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\nRange: bytes='+ str(start) +'-'+ str(end) +'\r\n\r\n' # request header
	else:
		request = 'GET '+ path +' HTTP/1.1\r\nHOST: '+ host +'\r\n\r\n' # request header

	soc.sendall(request.encode())

	if resume:
		file_to_write = open(dest, 'ab')
	else:
		file_to_write = open(dest, 'wb')
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
		downloaded[id] = rcvd_lngth
		if rcvd_lngth >= (end - start + 1): break
	soc.close()

# global dictionary to launch download based on connection type
connections = {'TCP': tcp_download, 'UDP': udp_download}

def print_stats(interval, target, start):
	'''
	function for printing downloading stats
	:param interval: interval in secs after which to print stats
	:param target: target number of bytes of whole download
	:param start: download starting time
	'''
	whole = 0
	finished = [False]*len(total)
	while True:
		time.sleep(interval)
		for i in range(len(total)):
			if finished[i]:
				continue
			if downloaded[i] >= total[i]:
				downloaded[i] = total[i] # better aesthetics by ignoring extra data
				finished[i] = True
			print('Connection ', str(i+1)+':', str(downloaded[i])+'/'+str(total[i])+', download speed: ', downloaded[i]/((time.time() - start)*1000), 'kb/s')
			whole += downloaded[i]
		if whole > target: whole = target # better aesthetics by ignoring extra data
		print('Total: ' + str(whole)+'/'+str(target),', download speed: ', whole/((time.time() - start)*1000), 'kb/s')
		print()
		if sum(finished) == len(finished) or whole >= target:
			break

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
	host, path, filename = parse_links(args.src, args.dest, args.resume)

	# using abbrevation convention
	connection_type = args.connection.upper()
	start_t = time.time()

	header = get_header(host, path)

	# process HEADER information
	if 'response' in header and header['response'].find('200') != -1:
		print('\nSuccessfully connected to', socket.gethostbyname(host))
	else:
		print('\nFailed! Server replied with error:', header['response'])
		exit(1)

	clength = -1
	if 'content-length' in header:
		clength = int(header['content-length'])
	else:
		print('\nServer did not return length of file. Using defaults: single connection')
		num_con = 1

	if not 'accept-ranges' in header:
		print('\nServer does not support ranges. Using defaults: single connection')
		num_con = 1


	# RESUME

	temporary_name = os.path.join(args.dest, '.'+filename.split('/')[-1]+'.tmp')
	if num_con == 1:
		temporary_name = filename

	intermediate_names = [] # files to hold data from each thread

	resumeable = False # flag to indicate if download is to be resumed
	if args.resume and 'accept-ranges' in header:
		resumeable, intermediate_names, ending_bytes = check_resume(temporary_name)

	if resumeable and intermediate_names: # single connection has no intermediates
		num_con = len(intermediate_names)
		print('Using',num_con,'connections for resuming...')
	elif args.resume and not resumeable:
		print('Resuming not possible.\n')

	# begin DOWNLOADING
	if resumeable: prefix = 'Resuming'
	else: prefix = 'Downloading'
	print('\n'+prefix, filename,'...\n')

	global downloaded, total
	downloaded = [0]*num_con
	total = [0]*num_con

	t = Thread(target=print_stats, args=(args.interval,clength, start_t))
	t.start()

	if num_con == 1: # avoid overheads
		if resumeable: # resumable already implies that server supports ranges
			start = os.stat(filename).st_size
		else:
			start = 0
		connections[connection_type](host, path, start, clength, filename, resumeable, 0)
		time.sleep(1) # for printing synchronization
		print('\nDownload Completed!')
		exit(0)

	# if more than one connections

	# THREADING
	threads = [] # list of threads
	multiple = clength // num_con # approx size of each chunk
	intermediate_data = []

	for i in range(num_con):
		print('Creating connection #', i+1)

		if not resumeable: # because otherwise we already have the names
			tmp_name = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=10))
			tmp_name = os.path.join(args.dest, '.'+tmp_name)
			# range calculation
			start = i*multiple
			end = (i+1)*multiple-1
			if i == num_con - 1:
				end = clength

			intermediate_names.append(tmp_name)

			intermediate_data.append(tmp_name+','+str(end))
		else:
			tmp_name = intermediate_names[i]

			if i is not 0:
				start = ending_bytes[i-1] + 1 # get start from previous' end
			else:
				start = 0
			start += os.stat(tmp_name).st_size # recovery size

			end = ending_bytes[i]

		threads.append( Thread(target=connections[connection_type], args=(host, path, start, end, tmp_name, resumeable, i)) )
		threads[-1].start()
	print()
	if not resumeable:
		with open(temporary_name, 'w') as temp:
			for name in intermediate_data:
				temp.write(name+'\n')

	# wait for threads to finish
	for thread in threads:
		thread.join()

	time.sleep(1) # for printing synchronization
	print('\nDownload Completed!')
	print('\nCombining chunks...')
	join_chunks(intermediate_names, filename)
	if temporary_name[-4:] == '.tmp':
		os.remove(temporary_name)
	print(filename, 'saved!')
