from socket import *
import _thread
import sys
import time
import os
from os import path
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import mimetypes
import random
import logging
import configparser


serverConfig = configparser.ConfigParser()
serverConfig.read("server.conf")
print(list(serverConfig["REDIRECT"]), type(serverConfig["DEFAULT"]["DocumentRoot"]))

formatter = logging.Formatter('%(message)s')

def date():
	now = datetime.now()
	stamp = mktime(now.timetuple())
	return time.asctime(time.localtime())

def setup_logger(name, log_file, level=logging.INFO):
	
	handler = logging.FileHandler(log_file)		   
	handler.setFormatter(formatter)

	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.addHandler(handler)

	return logger

access_logger = setup_logger('access_logger', serverConfig["DEFAULT"]["AccessLog"])
error_logger = setup_logger('error_logger',serverConfig["DEFAULT"]["ErrorLog"], logging.ERROR)
post_logger = setup_logger('post_logger', serverConfig["DEFAULT"]["PostLog"]) 
debug_logger = setup_logger('debug_logger', serverConfig["DEFAULT"]["DebugLog"], logging.DEBUG)
'''access_logger.info('This is testing access log')
post_logger.info('This is testing post log')
error_logger.error('this is testing error log')
debug_logger.debug('This is testing debug log')'''

status_code = {"200": "OK", "304": "Not Modified", "400": "Bad Request", "404": "Not Found", 
						"201": "Created", "204":"No Content", "301":"Moved Permanently", "307":"Temporary Redirect"}

portNumber = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', portNumber))
serverSocket.listen(int(serverConfig["DEFAULT"]["maxSimulteneousConnections"]))
print("HTTP server running on port ", portNumber)
debug_logger.debug("[" + str(date()) + "] HTTP server running on port " + str(portNumber))

def get_key(val, my_dict): 
	for key, value in my_dict.items(): 
		 if val == value: 
			 return key
	return None 

def create_hyperlink(port, page):
	return "<h1><a>http://127.0.0.1:" + str(port) + str(page) + "</a></h2>\r\n"

def recv_timeout(socket):	
	BUFF_SIZE = 4096
	data = b''
	while True:
		part = socket.recv(BUFF_SIZE)
		data+=part
		if (len(part) < BUFF_SIZE):
			break
	data = data.decode()
	return data

def date_mktime(string):
	return time.strptime(string, "%a %b %d %H:%M:%S %Y")


def parse_body(data):
	_, body = data.split("\r\n\r\n")
	return body

def parse_headers(words):
	headers = {}
	for i in range(1, len(words)-2):
		if(len(words[i]) > 2):
			for j in range(2, len(words[i])):
				words[i][1] += (" " + words[i][j])
		headers[words[i][0][:-1]] = words[i][1]
	return headers

def create_header(header, Content_len = 0, Content_type = "text/html", method = "GET", last_mod_date = None, header_flag_register = {}):
	header += ("Date: " + date()+"\r\n")
	header += ("Server: Http server (ubuntu)\r\n")
	header += ("Content-Length: " + str(Content_len) + "\r\n")
	header += ("Connection: Close\r\n")
	header += ("Content-Type: " + str(Content_type) + "\r\n")		
	if(header_flag_register.get("set_cookie_flag", None)):
		header += ("Set-Cookie: " + "TestCookie=" + str(random.randint(10000, 99999))+ "\r\n")
	
	if(method == "GET"):
		if(last_mod_date != None):
			try:
				header += ("Last-Modified: " + str(last_mod_date) + "\r\n")
			except Exception as e:
				error_logger.error("Server exception occurred", exc_info=True)
				print(e)
		header += ("\r\n")
	#print(header)	
	return header

def is_root_url(url):
	if(len(url) > 1 and url[1] == "/"):
		return True
	else:
		return False

def split_data(data):
	lines = data.split("\r\n")
	words = []
	for i in lines:
		words.append(i.split(" "))	
	return words

def client_thread(clientSocket, address):
	while(True):
		try:
			content_length = 0
			responseData = ""
			requestData = b''
			responseHeader = "HTTP/1.1"
			url = serverConfig["DEFAULT"]["DocumentRoot"]
			headers = {}
			requestBody = ""	
			header_flag_register = {"set_cookie_flag":False, "temp_redirect_flag":False, "per_redirect_flag":False}
			
			requestData= recv_timeout(clientSocket)
			print(requestData)
			requestWords = split_data(requestData)
			#print(requestWords)
			headers = parse_headers(requestWords)
			requestBody = parse_body(requestData)
			#print(headers)
			#print(requestBody)
			flag_status_code = {"200": False, "304": False, "400": False, "404": False, "201": False, "204": False, "301": False, "307": False}
			#set_cookie_flag = False
			if(requestWords[0][0] == "GET" or requestWords[0][0] == "HEAD"):
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				if(len(requestWords[0]) >= 2):
					info = requestWords[0][1].split("?") 
					#print(is_root_url(url))
					if(info[0] in list(serverConfig["REDIRECT"])):
						#print("PERMANT REDIRECT$$$$$")
						header_flag_register["per_redirect_flag"] = True
						flag_status_code["301"] = True
						url += serverConfig["REDIRECT"][info[0]]
					elif(info[0] in list(serverConfig["TEMP_REDIRECT"])):
						#print("TEMP_REDIRE$$$$$$$$$")
						flag_status_code["307"] = True 
						header_flag_register["temp_redirect_flag"] = True
						url += serverConfig["TEMP_REDIRECT"][info[0]]
					else:
						url += str(info[0])
				
				if(is_root_url(url)):
					try:
						requestedFile = open(url, "rb")
						content_length = requestedFile
						requestedFileType = mimetypes.MimeTypes().guess_type(url)[0]
					except:
						error_logger.error("Server exception occurred", exc_info=True)
						#code to send not found
						flag_status_code["404"] = True
				else:	
					#code to send bad request
					flag_status_code["400"] = True
				if(flag_status_code["404"]):
					not_found_page = open ("not_found.html", "r")
					file_text = not_found_page.read()
					content_length = len(file_text)
					responseHeader += (" 404 " + status_code["404"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					not_found_page.close()
					if(requestWords[0][0] == "GET"):
						responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				elif(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open ("bad_req.html", "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					if(requestWords[0][0] == "GET"):
						responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				elif(flag_status_code["301"]):
					redirect_page = open("redirect.html", "r")
					file_text = redirect_page.read()
					content_length = len(file_text)
					responseHeader += (" 301 " + status_code["301"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					redirect_page.close()
					responseHeader = responseHeader[:-2]
					responseHeader += ("Location: "+ url[1:] + "\r\n\r\n")
					if(requestWords[0][0] == "GET"):
						responseHeader += (create_hyperlink(portNumber, url[1:]) + file_text)
					print(responseHeader)
					clientSocket.sendall(responseHeader.encode())

				elif(flag_status_code["307"]):
					redirect_page = open("temp_redirect.html", "r")
					file_text = redirect_page.read()
					content_length = len(file_text)
					responseHeader += (" 307 " + status_code["307"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					redirect_page.close()
					responseHeader = responseHeader[:-2]
					responseHeader += ("Location: "+ url[1:] + "\r\n\r\n")
					if(requestWords[0][0] == "GET"):
						responseHeader += (create_hyperlink(portNumber, url[1:]) + file_text)
					print(responseHeader)
					clientSocket.sendall(responseHeader.encode())
				
				else:
					fileObject = requestedFile.read()
					requestedFile.close()
					requestedFileLen = len(fileObject)
					content_length = requestedFileLen
					#print(requestedFileLen)
					if(headers.get("If-Modified-Since", None)):
						Request_date = date_mktime(headers["If-Modified-Since"])
						Current_date = date_mktime(date())
						File_mod_date = path.getmtime(url)
						#print(mktime(Request_date), mktime(Current_date) ,File_mod_date)
						if(int(File_mod_date) <= int(mktime(Request_date))):
							flag_status_code["304"] = True
						else:
							flag_status_code["200"] = True

					if(flag_status_code["304"]):
						if(headers.get("Cookie", None) == None or "TestCookie" not in headers.get("Cookie", None)):
							header_flag_register["set_cookie_flag"] = True
						responseHeader += (" 304 " + status_code["304"] + "\r\n")
						responseHeader = create_header(responseHeader, requestedFileLen, requestedFileType,"GET", 
											time.ctime(path.getmtime(url)), header_flag_register)
						clientSocket.sendall(responseHeader.encode())
					else:
						if(headers.get("Cookie", None) == None or "TestCookie" not in headers.get("Cookie", None)):
							header_flag_register["set_cookie_flag"] = True
						responseHeader += (" 200 " + status_code["200"] + "\r\n")
						flag_status_code["200"] = True
						responseHeader = create_header(responseHeader, requestedFileLen, requestedFileType,"GET" 
											,time.ctime(path.getmtime(url)), header_flag_register)
						#print(responseHeader)
						if(requestWords[0][0] == "GET"):
							fileObject = responseHeader.encode() + fileObject
							#print(fileObject)
							clientSocket.sendall(fileObject)
						elif(requestWords[0][0] == "HEAD"):	
							clientSocket.sendall(responseHeader.encode())

			elif (requestWords[0][0] == "POST"):
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				url += requestWords[0][1]
				if(is_root_url):
					try:
						#post_logger.info(requestBody)
						responseHeader += ( " 204 " + status_code["204"] + "\r\n")
						flag_status_code["204"] = True
						responseHeader += create_header(responseHeader, 0, requestedFileType, "put")
						responseHeader += ("Content-Location: " + url[1:] + "\r\n\r\n")
					except Exception as e:
						error_logger.error("Server exception occurred", exc_info=True)
						pass
				else:	
					#code to send bad request
					flag_status_code["400"] = True

				if(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open ("bad_req.html", "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())			
				else:	
					clientSocket.sendall(responseHeader.encode())			
					
				post_logger.info(str(address[0]) + " [" + str(date()) + 
						'] "' + ' '.join(requestWords[0]) + '" ' + get_key(True, flag_status_code) + " " + str(content_length) + " " + str(requestBody))


			elif (requestWords[0][0] == "PUT"):	
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				url += requestWords[0][1]
				if(is_root_url):
					try:
						flag = path.exists(url)
						requestedFile = open(url, "w+")
						requestedFileType = mimetypes.MimeTypes().guess_type(url)[0]
						requestedFile.write(requestBody)
						if(flag):
							responseHeader += ( " 204 " + status_code["204"] + "\r\n")
							flag_status_code["204"] = True
						else:
							responseHeader += ( " 201 " + status_code["201"] + "\r\n")
							flag_status_code["201"] = True
						responseHeader += create_header(responseHeader, 0, requestedFileType, "put")
						responseHeader += ("Content-Location: " + url[1:] + "\r\n\r\n")
					except Exception as e:
						error_logger.error("Server exception occurred", exc_info=True)
						pass
				else:	
					#code to send bad request
					flag_status_code["400"] = True

				if(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open ("bad_req.html", "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())			
				else:	
					clientSocket.sendall(responseHeader.encode())			
			
			elif(requestWords[0][0] == "DELETE"):
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				url += requestWords[0][1]
				if(is_root_url):
					try:
						flag = path.exists(url)
						requestedFileType = mimetypes.MimeTypes().guess_type(url)[0]
						if(flag):
							try:
								os.remove(url)	
								responseHeader += ( " 204 " + status_code["204"] + "\r\n")
								responseHeader += create_header(responseHeader, 0, requestedFileType, "put")
								responseHeader += ("Content-Location: " + url[1:] + "\r\n\r\n")
								flag_status_code["204"] = True
							except Exception as e:
								error_logger.error("Server exception occurred", exc_info=True)
								print(e)	
								flag_status_code["404"] = True
						else:
							flag_status_code["404"] = True
					except Exception as e:
						error_logger.error("Server exception occurred", exc_info=True)
						print(e)
				else:	
					#code to send bad request
					flag_status_code["400"] = True

				if(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open ("bad_req.html", "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				elif(flag_status_code["404"]):
					not_found_page = open ("not_found.html", "r")
					file_text = not_found_page.read()
					content_length = len(file_text)
					responseHeader += (" 404 " + status_code["404"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					not_found_page.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				else: #when status code is 204 No content	
					clientSocket.sendall(responseHeader.encode())
			log_flag = False
			if(get_key(True, flag_status_code) != None):
				log_flag = True
				access_logger.info(str(address[0]) + " [" + str(date()) + 
									'] "' + ' '.join(requestWords[0]) + '" ' + get_key(True, flag_status_code) + " " + str(content_length))
			clientSocket.close()
		except Exception as e:
			if(get_key(True, flag_status_code) != None and not log_flag):
				access_logger.info(str(address[0]) + " [" + str(date()) + 
									'] "' + ' '.join(requestWords[0]) + '" ' + get_key(True, flag_status_code) + " " + str(content_length))
			clientSocket.close()
			if(str(e) != "[Errno 9] Bad file descriptor"):
				#print("HERE")
				error_logger.error("Server exception occurred", exc_info=True)
			break


while True:
	try:
		clientSocket, address = serverSocket.accept()
		print("connected to", address)
		debug_logger.debug("[" + str(date()) + "] connected to IP: " + str(address[0]) + " Port: " + str(address[1]))
		_thread.start_new_thread(client_thread, (clientSocket, address, ))
	except:
		#print(e)
		print("\n*****Http server stopped*****")
		debug_logger.debug("[" + str(date()) + "] HTTP server stopped")
		break
serverSocket.close()
'''def recv_timeout(the_socket,timeout=0.3):
	the_socket.setblocking(0) 
	total_data=[];
	data=b'';
	begin=time.time()
	while 1:
		if total_data and time.time()-begin > timeout:
			break
		
		elif time.time()-begin > timeout*2:
			break	
		try:
			data = the_socket.recv(8192)
			if data:
				total_data.append(data.decode())
				begin=time.time()
			else:
				time.sleep(0.1)
		except:
			pass
	
	return ''.join(total_data)'''

