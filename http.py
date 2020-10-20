from socket import *
import _thread
import sys
import time
from os import path
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import mimetypes

status_code = {"200": "OK", "304": "Not Modified", "400": "Bad Request", "404": "Not Found", "201": "Created", "204":"No Content"}


portNumber = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', portNumber))
serverSocket.listen(20)
print("HTTP server running on port ", portNumber)

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

def date():
	now = datetime.now()
	stamp = mktime(now.timetuple())
	return time.asctime(time.localtime())

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

def create_header(header, Content_len = 0, Content_type = "text/html", method = "GET", last_mod_date = None):
	header += ("Date: " + date()+"\r\n")
	header += ("Server: Http server (ubuntu)\r\n")
	header += ("Content-Length: " + str(Content_len) + "\r\n")
	header += ("Connection: Close\r\n")
	header += ("Content-Type: " + str(Content_type) + "\r\n")
	if(method == "GET"):
		if(last_mod_date != None):
			try:
				header += ("Last-Modified: " + str(last_mod_date) + "\r\n")
			except Exception as e:
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

def client_thread(clientSocket):
	while(True):
		try:
			responseData = ""
			requestData = b''
			responseHeader = "HTTP/1.1"
			url = "."
			headers = {}
			requestBody = ""	
			requestData = recv_timeout(clientSocket)
			requestWords = split_data(requestData)
			#print(requestWords)
			headers = parse_headers(requestWords)
			requestBody = parse_body(requestData)
			print(headers)
			#print(requestBody)
			flag_status_code = {"200": False, "304": False, "400": False, "404": False, "201": False, "204": False}
			if(requestWords[0][0] == "GET"):
				version = "HTTP/1.1"
				if(len(requestWords[0]) == 3):
					version = requestWords[0][2]
				if(len(requestWords[0]) >= 2):
					info = requestWords[0][1].split("?") 
					url += str(info[0])
				#print(is_root_url(url))
				if(is_root_url(url)):
					try:
						requestedFile = open(url, "rb")
						requestedFileType = mimetypes.MimeTypes().guess_type(url)[0]
					except:
						#code to send not found
						flag_status_code["404"] = True
				else:	
					#code to send bad request
					flag_status_code["400"] = True
				if(flag_status_code["404"]):
					responseHeader += (" 404 " + status_code["404"] + "\r\n")
					responseHeader = create_header(responseHeader)
					not_found_page = open ("not_found.html", "r")
					file_text = not_found_page.read()
					not_found_page.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())
				elif(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open ("bad_req.html", "r")
					file_text = bad_req.read()
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())			
				else:
					fileObject = requestedFile.read()
					requestedFileLen = len(fileObject)
					#print(requestedFileLen)
					if(headers.get("If-Modified-Since", None)):
						Request_date = date_mktime(headers["If-Modified-Since"])
						Current_date = date_mktime(date())
						File_mod_date = path.getmtime(url)
						print(mktime(Request_date), mktime(Current_date) ,File_mod_date)
						if(int(File_mod_date) <= int(mktime(Request_date))):
							flag_status_code["304"] = True
						else:
							flag_status_code["200"] = True

					if(flag_status_code["304"]):
						responseHeader += (" 304 " + status_code["304"] + "\r\n")
						responseHeader = create_header(responseHeader, requestedFileLen, requestedFileType,"GET", time.ctime(path.getmtime(url)))
						clientSocket.sendall(responseHeader.encode())
					else:
						responseHeader += (" 200 " + status_code["200"] + "\r\n")
						responseHeader = create_header(responseHeader, requestedFileLen, requestedFileType,"GET" ,time.ctime(path.getmtime(url)))
						#print(responseHeader)
						fileObject = responseHeader.encode() + fileObject
						#print(fileObject)
						clientSocket.sendall(fileObject)

			elif (requestWords[0][0] == "POST"):
				print("Executing post....")	

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
						responseHeader += create_header(responseHeader, 0, requestedFileType, "post")
						responseHeader += ("Content-Location: " + url[1:] + "\r\n\r\n")
					except:
						pass
				else:	
					#code to send bad request
					flag_status_code["400"] = True

				if(flag_status_code["400"]):	
					responseHeader += (" 400 " + status_code["400"] + "\r\n")
					responseHeader = create_header(responseHeader)
					bad_req = open ("bad_req.html", "r")
					file_text = bad_req.read()
					bad_req.close()
					responseHeader += file_text
					clientSocket.sendall(responseHeader.encode())			
				else:	
					clientSocket.sendall(responseHeader.encode())			

			clientSocket.close()
		except Exception as e:
			print(e)
			clientSocket.close()
			break


while True:
	try:
		clientSocket, address = serverSocket.accept()
		print("connected to", address)
		_thread.start_new_thread(client_thread, (clientSocket, ))
	except:
		#print(e)
		print("\n*****Http server stopped*****")
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

