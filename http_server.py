from socket import *
from threading import *
import sys
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import mimetypes

status_code = {"200": "OK", "304": "Not Modified", "400": "Bad Request", "404": "Not Found"}

portNumber = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', portNumber))
serverSocket.listen(20)
print("HTTP server running on port ", portNumber)

def date():
	now = datetime.now()
	stamp = mktime(now.timetuple())
	return format_date_time(stamp)


def create_header(header, Content_len = 0, Content_type = "text/html"):
	header += ("Date: " + date()+"\r\n")
	header += ("Server: Http server (ubuntu)\r\n")
	header += ("Content-Length: " + str(Content_len) + "\r\n")
	header += ("Connection: Close\r\n")
	header += ("Content-Type: " + str(Content_type) + "\r\n")
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

try:
	while(True):
		clientSocket, address = serverSocket.accept()
		print("connected to", address)
		responseData = ""
		responseHeader = "HTTP/1.1"
		url = "."
		requestData = clientSocket.recv(1024)
		requestData = requestData.decode()[:-2]
		requestWords = split_data(requestData)
		#print(requestWords)
		flag_status_code = {"200": False, "304": False, "400": False, "404": False}
		if(requestWords[0][0] == "GET"):
			version = "HTTP/1.1"
			if(len(requestWords[0]) == 3):
				version = requestWords[0][2]
			if(len(requestWords[0]) >= 2):
				url += str(requestWords[0][1])
			#print(is_root_url(url))
			if(is_root_url(url)):
				try:
					requestedFile = open(url, "r")
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
				clientSocket.sendall(responseHeader.encode())
			elif(flag_status_code["400"]):	
				responseHeader += (" 400 " + status_code["400"] + "\r\n")
				responseHeader = create_header(responseHeader)
				clientSocket.sendall(responseHeader.encode())			
			else:
				fileObject = requestedFile.read()
				requestedFileLen = len(fileObject)
				#print(requestedFileLen)
				responseHeader += (" 200 " + status_code["200"] + "\r\n")
				responseHeader = create_header(responseHeader, requestedFileLen, requestedFileType)
				#print(responseHeader)
				fileObject = responseHeader + fileObject
				#print(fileObject)
				clientSocket.sendall(fileObject.encode())
		clientSocket.close()
except:
	clientSocket.close()
