from urllib.parse import urlparse

import os

'''
Contains utility functions for side processing not directly linked to networking
'''

def parse_links(url, dest):
	'''
	function to extract relevant data from the full given link
	:param url: full url to download file form
	:param dest: destination folder to save files to; for duplicate files matching
	:return: host name, path to source file, and destination file name
	'''
	url = urlparse(url)
	host = url.netloc
	path = url.path

	if url.scheme == '':
		host = url.path.split('/')[0] # if scheme is not present, domain comes before first slash '/'
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