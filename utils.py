import os

'''
Contains utility functions for side processing not directly linked to networking
'''

def parse_links(link, dest, resume):
	'''
	function to extract relevant data from the full given link
	:param link: full url to download file form
	:param dest: destination folder to save files to; for duplicate files matching
	:return: host name, path to source file, and destination file name
	'''
	host_start = 0
	if link.find('http') != -1:
		host_start = link.find('//') + 2
	host_end = link[host_start:].find('/') + host_start

	host = link[host_start: host_end]

	path = link[host_end:]

	if path == '':
		path = '/' # request root i.e., index.html by convention

	filename = path.split('/')[-1] # filname comes last
	if filename == '': # root filename
		filename = 'index.html'

	# check if file already exists, choose another name
	full_path = os.path.join(dest, filename)
	i = 1
	while os.path.isfile(full_path) and not resume:
		full_path = os.path.join(dest, '('+str(i)+') '+filename)
		i += 1

	return host, path, full_path


def check_resume(src):
	'''
	function for checking resuming feasibility by checking if all files exist
	:param src: tmp intermedate file name which has data about other files
	'''

	print('\nChecking files for resuming...')
	resumeable = False
	intermediates = []
	ending_bytes = []

	# .tmp file indicates more than multiple connections
	# because for single connection, no tmp file

	if os.path.exists(src) and src[-4:] == '.tmp': # can only look for temporary files when multi threaded
		with open(src, 'r') as files:
			for line in files.readlines():
				tmp_file, end = line.strip().split(',')
				if not os.path.exists(tmp_file):
					intermediates = []
					ending_bytes = []
					break
				# if exists, get the data
				intermediates.append(tmp_file.strip())
				ending_bytes.append(int(end))
			else:
				resumeable = True
	else: # if num of connections is 1, actual file will decide resuming
		resumeable = os.path.exists(src)

	return resumeable, intermediates, ending_bytes

def join_chunks(files, filename):
	'''
	function for combining files into a single output and delete temporary files
	:param files: list of intermediate file names
	:param filename: output file name
	'''
	with open(filename, 'wb') as dest:
		for line in files:
			file = line.split(',')[0]
			src = open(file, 'rb')
			dest.write(src.read())

			os.remove(file)
