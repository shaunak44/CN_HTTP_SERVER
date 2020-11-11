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
import base64 
import sched
serverConfig = configparser.ConfigParser()
serverConfig.read("server.conf")

formatter = logging.Formatter('%(message)s')

class Timer():
	def __init__(self, timeout_val):
		self.default = -1
		self.start_time = self.default
		self.timeout_val = timeout_val
	def start(self):
		self.start_time = time.time()
	def stop(self):
		self.start_time = self.default
	def running(self):
		return self.start_time != self.default
	def timeout(self):
		if self.running():
			return time.time() - self.start_time >= self.timeout_val
		else:
			return False

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

status_code = {"200": "OK", "304": "Not Modified", "400": "Bad Request", "404": "Not Found", "401":"Unauthorized", "403":"Forbidden",
						"201": "Created", "204":"No Content", "301":"Moved Permanently", "307":"Temporary Redirect", "206": "Partial Content", 
						"416": "Range Not Satisfiable", "501": "Not Implemented"}

portNumber = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', portNumber))
serverSocket.listen(int(serverConfig["DEFAULT"]["maxSimulteneousConnections"]))
print("HTTP server running on Port", portNumber)
print("Press CTRL + C to Exit.")
debug_logger.debug("[" + str(date()) + "] HTTP server running on port " + str(portNumber))
timer = Timer(1)

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
		timer.start()
		part = socket.recv(BUFF_SIZE)
		if(timer.timeout()):
			timer.stop()
			return None
		data+=part
		if (len(part) < BUFF_SIZE):
			break
	data = data.decode()
	return data

def range_parser(ranges):
	try:
		d = {}
		_, ranges = ranges.split("=")
		range_list = ranges.split(",")
		for i in range_list:
			start, end = i.split("-")
			d[int(start)] = int(end)
		return d
	except:
		return None


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
		cookie_file = open("cookies.txt", "r+")
		cookie_list = cookie_file.read().splitlines()
		cookie_file.close()	
		cookie_val = str(random.randint(10000, 99999))
		while cookie_val in cookie_list:
			cookie_val = str(random.randint(10000, 99999))		
		cookie_file = open("cookies.txt", "a")
		cookie_file.write(cookie_val + "\n")
		cookie_file.close()
		header += ("Set-Cookie: " + "TestCookie=" + cookie_val + "\r\n")
	
	if(method == "GET"):
		if(last_mod_date != None):
			try:
				header += ("Last-Modified: " + str(last_mod_date) + "\r\n")
			except Exception as e:
				msg =  str(date()) + " Server exception Occurred"
				error_logger.error(msg, exc_info=True)
				error_logger.error("--------------------------------------------------------------------------------")
				print(e)
		header += ("\r\n")
	return header

def is_root_url(url):
	if(len(url) > 1 and url[len(serverConfig["DEFAULT"]["DocumentRoot"])] == "/"):
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
			serverConfig = configparser.ConfigParser()
			serverConfig.read("server.conf")
			content_length = 0
			responseData = ""
			requestData = b''
			responseHeader = "HTTP/1.1"
			url = serverConfig["DEFAULT"]["DocumentRoot"]
			headers = {}
			requestBody = ""	
			header_flag_register = {"set_cookie_flag":False, "temp_redirect_flag":False, "per_redirect_flag":False}
			global log_flag
			method_flag = {"get": True, "post": True, "put": True, "delete": True, "head": True}		
			requestData= recv_timeout(clientSocket)
			if(requestData == None):
				responseHeader += (" 408 " + "Request Timeout" + "\r\n")
				responseHeader += ("Date: " + date()+"\r\n")
				responseHeader += ("Server: Http server (ubuntu)\r\n")
				responseHeader += ("Connection: Close\r\n\r\n")
				clientSocket.sendall(responseHeader.encode())
				clientSocket.close()	
				access_logger.info(str(address[0]) + " [" + str(date()) + 
									'] "' + "Request Timed Out"  + '" ' + "408" + " " + "0")
				break
			requestWords = split_data(requestData)
			headers = parse_headers(requestWords)
			try:
				requestBody = parse_body(requestData)
			except:
				pass
			flag_status_code = {"304": False, "400": False, "404": False, "201": False, "204": False, "301": False, "307": False, 
									"401": False, "403": False, "200": False, "416": False,"206": False, "501":False} 
				
			if(requestWords[0][1] in list(serverConfig["FORBIDDEN_FILES"])):
				flag_status_code["403"] = True
				temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/forbidden.html"
				not_found_page = open (temp_url, "r")
				file_text = not_found_page.read()
				content_length = len(file_text)
				responseHeader += (" 403 " + status_code["403"] + "\r\n")
				responseHeader = create_header(responseHeader, content_length)
				responseHeader += file_text
				clientSocket.sendall(responseHeader.encode())
				method_flag["get"] = False
				method_flag["post"] = False
				method_flag["head"] = False
				method_flag["delete"] = False
				method_flag["put"] = False
			
			elif(requestWords[0][1] in list(serverConfig["AUTHORIZED_FILES"]) or requestWords[0][0] == "PUT" or requestWords[0][0] == "DELETE"):
				flag_status_code["401"] = True
				credentials = headers.get("Authorization", None)
				if(not credentials):
					responseHeader += (" 401 " + status_code["401"] + "\r\n")
					responseHeader = create_header(responseHeader, 0)
					responseHeader = responseHeader[:-2]
					responseHeader += 'WWW-Authenticate: Basic realm="Access to staging site"'
					responseHeader += ("\r\n\r\n")
					flag_status_code["401"] = True
					method_flag["get"] = False
					method_flag["post"] = False
					method_flag["head"] = False
					method_flag["delete"] = False
					method_flag["put"] = False
					clientSocket.sendall(responseHeader.encode())
				else:
					type_, credentials = credentials.split(" ")
					credentials_bytes = credentials.encode("ascii") 
					credential_sample_bytes = base64.b64decode(credentials_bytes)
					credentials = credential_sample_bytes.decode("ascii")
					username, password = credentials.split(":")
					if(username in list(serverConfig["AUTHORIZED_USERS"]) 
						and serverConfig["AUTHORIZED_USERS"][username] == password):
						flag_status_code["401"] = False
					else:	
						responseHeader += (" 401 " + status_code["401"] + "\r\n")
						responseHeader = create_header(responseHeader, 0)
						responseHeader = responseHeader[:-2]
						responseHeader += 'WWW-Authenticate: Basic realm="Access to staging site"'
						responseHeader += ("\r\n\r\n")
						flag_status_code["401"] = True
						method_flag["get"] = False
						method_flag["post"] = False
						method_flag["head"] = False
						method_flag["delete"] = False
						method_flag["put"] = False
						clientSocket.sendall(responseHeader.encode())

			


			#set_cookie_flag = False
			if((requestWords[0][0] == "GET" and method_flag["get"]) or (requestWords[0][0] == "HEAD" and method_flag["head"])):
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				if(len(requestWords[0]) >= 2):
					info = requestWords[0][1].split("?") 
					if(info[0] in list(serverConfig["REDIRECT"])):
						header_flag_register["per_redirect_flag"] = True
						flag_status_code["301"] = True
						url += serverConfig["REDIRECT"][info[0]]
					elif(info[0] in list(serverConfig["TEMP_REDIRECT"])):
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
						msg =  str(date()) + " Server exception Occurred"
						error_logger.error(msg, exc_info=True)
						error_logger.error("--------------------------------------------------------------------------------")
						#code to send not found
						flag_status_code["404"] = True
				else:	
					#code to send bad request
					flag_status_code["400"] = True
				if(flag_status_code["404"]):
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/not_found.html"
					not_found_page = open (temp_url, "r")
					file_text = not_found_page.read()
					content_length = len(file_text)
					responseHeader += (" 404 " + status_code["404"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					not_found_page.close()
					if(requestWords[0][0] == "GET"):
						responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				elif(flag_status_code["400"]):	
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/bad_req.html"
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open (temp_url, "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					if(requestWords[0][0] == "GET"):
						responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				elif(flag_status_code["301"]):
					temp_len = len(serverConfig["DEFAULT"]["DocumentRoot"])
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/redirect.html"
					redirect_page = open(temp_url, "r")
					file_text = redirect_page.read()
					content_length = len(file_text)
					responseHeader += (" 301 " + status_code["301"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					redirect_page.close()
					responseHeader = responseHeader[:-2]
					responseHeader += ("Location: "+ url[temp_len:] + "\r\n\r\n")
					if(requestWords[0][0] == "GET"):
						responseHeader += (create_hyperlink(portNumber, url[1:]) + file_text)
					clientSocket.sendall(responseHeader.encode())

				elif(flag_status_code["307"]):
					temp_len = len(serverConfig["DEFAULT"]["DocumentRoot"])
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/temp_redirect.html"
					redirect_page = open(temp_url, "r")
					file_text = redirect_page.read()
					content_length = len(file_text)
					responseHeader += (" 307 " + status_code["307"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					redirect_page.close()
					responseHeader = responseHeader[:-2]
					responseHeader += ("Location: "+ url[temp_len:] + "\r\n\r\n")
					if(requestWords[0][0] == "GET"):
						responseHeader += (create_hyperlink(portNumber, url[1:]) + file_text)
					clientSocket.sendall(responseHeader.encode())
	
				else:
					fileObject = requestedFile.read()
					requestedFile.close()
					requestedFileLen = len(fileObject)
					content_length = requestedFileLen
					if(headers.get("If-Modified-Since", None)):
						Request_date = date_mktime(headers["If-Modified-Since"])
						Current_date = date_mktime(date())
						File_mod_date = path.getmtime(url)
						if(int(File_mod_date) <= int(mktime(Request_date))):
							flag_status_code["304"] = True
						else:
							flag_status_code["200"] = True
					elif(headers.get("If-Range", None) and headers.get("Range", None)): 
						Request_date = date_mktime(headers["If-Range"])
						Current_date = date_mktime(date())
						File_mod_date = path.getmtime(url)
						if(int(File_mod_date) <= int(mktime(Request_date))):
							flag_status_code["206"] = True
						else:
							flag_status_code["200"] = True
							

					if(flag_status_code["304"]):
						if(headers.get("Cookie", None) == None or "TestCookie" not in headers.get("Cookie", None)):
							header_flag_register["set_cookie_flag"] = True
						responseHeader += (" 304 " + status_code["304"] + "\r\n")
						responseHeader = create_header(responseHeader, requestedFileLen, requestedFileType,"GET", 
											time.ctime(path.getmtime(url)), header_flag_register)
						clientSocket.sendall(responseHeader.encode())

					elif(flag_status_code["206"]):
						ranges = headers.get("Range")
						ranges_dic = range_parser(ranges)
						if(ranges_dic == None):
							flag_status_code["416"] = True
							responseHeader += (" 416 " + status_code["416"] + "\r\n\r\n")
							clientSocket.sendall(responseHeader.encode())
						elif(len(ranges_dic) == 1):
							for i in ranges_dic:
								end = ranges_dic[i]
								start = i
								length = ranges_dic[i] - i
							responseHeader += (" 206 " + status_code["206"] + "\r\n")
							responseHeader = create_header(responseHeader, length, requestedFileType,"GET", 
												time.ctime(path.getmtime(url)), header_flag_register)
							
							if(requestWords[0][0] == "GET"):
								fileObject = responseHeader.encode() + fileObject[start:end]
								clientSocket.sendall(fileObject)
							elif(requestWords[0][0] == "HEAD"):	
								clientSocket.sendall(responseHeader.encode())
						elif(len(ranges_dic) > 1):
							body = b''
							length = 0
							for i in ranges_dic:
								start = i
								end = ranges_dic[i]
								length += (end - start)
								string_separator = (b'\r\n--HTTPSERVERSEPARATOR\r\n' + b'Content-Type: ' + str(requestedFileType).encode() 
														+ b'\r\nContent-Range: bytes ' + str(start).encode() + b"-" + str(end).encode() + 
																b'/' + str(requestedFileLen).encode() + b'\r\n\r\n')
								body += (string_separator + fileObject[start:end])
							body += b'\r\n--HTTPSERVERSEPARATOR--\r\n'
							length += (len(ranges_dic)*len(string_separator) + 24)
							responseHeader += (" 206 " + status_code["206"] + "\r\n")
							responseHeader = create_header(responseHeader, length, "multipart/byteranges; boundary=HTTPSERVERSEPARATOR","GET", 
												time.ctime(path.getmtime(url)), header_flag_register)
							
							if(requestWords[0][0] == "GET"):
								fileObject = responseHeader.encode() + body
								clientSocket.sendall(fileObject)
							elif(requestWords[0][0] == "HEAD"):	
								clientSocket.sendall(responseHeader.encode())
							


					else:
						if(headers.get("Cookie", None) == None or "TestCookie" not in headers.get("Cookie", None)):
							header_flag_register["set_cookie_flag"] = True
						responseHeader += (" 200 " + status_code["200"] + "\r\n")
						flag_status_code["200"] = True
						responseHeader = create_header(responseHeader, requestedFileLen, requestedFileType,"GET" 
											,time.ctime(path.getmtime(url)), header_flag_register)
						if(requestWords[0][0] == "GET"):
							fileObject = responseHeader.encode() + fileObject
							clientSocket.sendall(fileObject)
						elif(requestWords[0][0] == "HEAD"):	
							clientSocket.sendall(responseHeader.encode())

			elif (requestWords[0][0] == "POST" and method_flag["post"]):
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				url += requestWords[0][1]
				if(is_root_url(url)):
					try:
						responseHeader += ( " 204 " + status_code["204"] + "\r\n")
						flag_status_code["204"] = True
						responseHeader += create_header(responseHeader, 0, "text/html", "post")
						responseHeader += ("Content-Location: " + url[1:] + "\r\n\r\n")
					except Exception as e:
						msg =  str(date()) + " Server exception Occurred"
						error_logger.error(msg, exc_info=True)
						error_logger.error("--------------------------------------------------------------------------------")
						pass
				else:	
					#code to send bad request
					flag_status_code["400"] = True

				if(flag_status_code["400"]):	
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/bad_req.html"
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open (temp_url, "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())			
				else:	
					clientSocket.sendall(responseHeader.encode())			
					
				post_logger.info(str(address[0]) + " [" + str(date()) + 
						'] "' + ' '.join(requestWords[0]) + '" ' + get_key(True, flag_status_code) + " " + str(content_length) + " " + str(requestBody))


			elif (requestWords[0][0] == "PUT" and method_flag["put"]):	
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				url += requestWords[0][1]
				if(is_root_url(url)):
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
						msg =  str(date()) + " Server exception Occurred"
						error_logger.error(msg, exc_info=True)
						error_logger.error("--------------------------------------------------------------------------------")
						pass
				else:	
					#code to send bad request
					flag_status_code["400"] = True

				if(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/bad_req.html"
					bad_req = open (temp_url, "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())			
				else:	
					clientSocket.sendall(responseHeader.encode())			
			
			elif(requestWords[0][0] == "DELETE" and method_flag["delete"]):
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				url += requestWords[0][1]
				if(is_root_url(url)):
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
								msg =  str(date()) + " Server exception Occurred"
								error_logger.error(msg, exc_info=True)
								error_logger.error("--------------------------------------------------------------------------------")
				
								flag_status_code["404"] = True
						else:
							flag_status_code["404"] = True
					except Exception as e:
						msg =  str(date()) + " Server exception Occurred"
						error_logger.error(msg, exc_info=True)
						error_logger.error("--------------------------------------------------------------------------------")
				else:	
					#code to send bad request
					flag_status_code["400"] = True

				if(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/bad_req.html"
					bad_req = open (temp_url, "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				elif(flag_status_code["404"]):
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/not_found.html"
					not_found_page = open (temp_url, "r")
					file_text = not_found_page.read()
					content_length = len(file_text)
					responseHeader += (" 404 " + status_code["404"] + "\r\n")
					responseHeader = create_header(responseHeader, len(file_text))
					not_found_page.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				else: #when status code is 204 No content	
					clientSocket.sendall(responseHeader.encode())

			elif(requestWords[0][0]):
				url += requestWords[0][1]
				if(is_root_url(url)):
					responseHeader += (" 501 " + status_code["501"] + "\r\n")
					flag_status_code["501"] = True
					responseHeader = create_header(responseHeader)
					clientSocket.sendall(responseHeader.encode())
				else:
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					flag_status_code["400"] = True
					responseHeader = create_header(responseHeader)
					temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/bad_req.html"
					bad_req = open (temp_url, "r")
					file_text = bad_req.read()
					content_length = len(file_text)
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())	

			else:
				responseHeader += (" 400 " + status_code["400"] + "\r\n")
				flag_status_code["400"] = True
				responseHeader = create_header(responseHeader)
				temp_url = serverConfig["DEFAULT"]["DocumentRoot"] + "/bad_req.html"
				bad_req = open (temp_url, "r")
				file_text = bad_req.read()
				content_length = len(file_text)
				bad_req.close()
				responseHeader += file_text
				clientSocket.sendall(responseHeader.encode())
				
			
			log_flag = False
			counter = 0
			if(get_key(True, flag_status_code) != None):
				log_flag = True
				counter+=1
				access_logger.info(str(address[0]) + " [" + str(date()) + 
									'] "' + ' '.join(requestWords[0]) + '" ' + get_key(True, flag_status_code) + " " + str(content_length))
			socket_close_flag = False
			clientSocket.close()
			socket_close_flag = True
		except Exception as e:
			if(get_key(True, flag_status_code) != None and not log_flag):
				access_logger.info(str(address[0]) + " [" + str(date()) + 
									'] "' + ' '.join(requestWords[0]) + '" ' + get_key(True, flag_status_code) + " " + str(content_length))
			if(socket_close_flag == False):
				clientSocket.close()
			if(str(e) != "[Errno 9] Bad file descriptor"):
				msg =  str(date()) + " Server exception Occurred"
				error_logger.error(msg, exc_info=True)
				error_logger.error("--------------------------------------------------------------------------------")
			break

while True:
	try:
		try:
			clientSocket, address = serverSocket.accept()
		except:
			raise Exception("Sorry, no numbers below zero")
		debug_logger.debug("[" + str(date()) + "] connected to IP: " + str(address[0]) + " Port: " + str(address[1]))
		_thread.start_new_thread(client_thread, (clientSocket, address,))
	except Exception as e:
		print("\n*****Http server stopped*****")
		debug_logger.debug("[" + str(date()) + "] HTTP server stopped")
		break
serverSocket.close()
