import os

'''
Contains utility functions for side processing not directly linked to networking
'''

def parse_links(link, dest):
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
	while os.path.isfile(full_path):
		full_path = os.path.join(dest, '('+str(i)+') '+filename)
		i += 1

	return host, path, full_path

def join_chunks(files, filename):
	with open(filename, 'wb') as dest:
		for file in files:
			src = open(file, 'rb')
			dest.write(src.read())

			os.remove(file)