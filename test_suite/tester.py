import requests
from threading import *
import unittest
from time import sleep
from socket import *

port = 12345
def headerMaker(method, requestedFile):
	request = method + " " + requestedFile + " " + "HTTP/1.1" + "\r\n"
	request += "Host: 127.0.0.1/" + str(port) + "\r\n"
	request += "User-Agent: Tester v1.0" + "\r\n"
	request += "Accept: image/webp,*/*" + "\r\n"
	request += "Accept-Language: en-US,en;q=0.5" + "\r\n"
	request += "Accept-Encoding: gzip, deflate" + "\r\n"
	request += "Connection: keep-alive" + "\r\n"
	request += "\r\n"
	return request



#response = requests.get('http://127.0.0.1:12345/index3.html')
class GetRequestMaker(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(GetRequestMaker, self).__init__(*args, **kwargs)
		self.recvd = 0

	def test_simple_get(self):
		print("\nSending simple GET request")
		response = requests.get('http://127.0.0.1:12345/index.html')
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple GET working correctly")
		except Exception as e:	
			print("The simple GET not working correctly", e)

	def test_simple_get_with_auth(self):	
		print("\nSending simple GET request with Valid Auth")
		response = requests.get('http://127.0.0.1:12345/index3.html', auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple GET working correctly with Valid Auth")
		except Exception as e:	
			print("The simple GET not working correctly with Valid Auth", e)
			
	def test_simple_get_with_inauth(self):	
		print("\nSending simple GET request with Invalid Auth")
		response = requests.get('http://127.0.0.1:12345/index3.html', auth=requests.auth.HTTPBasicAuth('temp', 'temp'))
		try:
			self.assertEqual(response.status_code, 401)
			print("The simple GET working correctly with Invalid Auth")
		except Exception as e:	
			print("The simple GET not working correctly with Invalid Auth", e)

	def test_simple_get_with_temp_redirect(self):	
		print("\nSending simple GET request for temporary redirect")
		response = requests.get('http://127.0.0.1:12345/index2.html')
		try:
			self.assertEqual(str(response.history[0]), "<Response [307]>")
			print("The simple GET working correctly for temporary redirect")
		except Exception as e:	
			print("The simple GET not working correctly for temporary redirect", e)
	
	def test_simple_get_with_per_redirect(self):	
		print("\nSending simple GET request for permanent redirect")
		response = requests.get('http://127.0.0.1:12345/index1.html')
		try:
			self.assertEqual(str(response.history[0]), "<Response [301]>")
			print("The simple GET working correctly for permanent redirect")
		except Exception as e:	
			print("The simple GET not working correctly for permanent redirect", e)

	def multiple_get(self, num):
		for i in range (0, num):
			response = requests.get('http://127.0.0.1:12345/index.html')
			if response.status_code == 200:
				self.recvd += 1
	
	def test_simple_get_with_25_requests(self):
		print("\nSending multiple 25 GET requests")
		for i in range(0, 5):
			Thread(target=self.multiple_get, args=(5, )).start()
		sleep(0.1)
		try:
			self.assertEqual(self.recvd, 25)
			print("The simple GET with 25 requests working correctly")
		except Exception as e:	
			print("The simple GET with 25 requests not working correctly", e)
		self.recvd = 0
	
	def test_simple_get_with_100_requests(self):
		print("\nSending multiple 100 GET requests")
		for i in range(0, 10):
			Thread(target=self.multiple_get, args=(10, )).start()
		sleep(0.25)
		try:
			self.assertEqual(self.recvd, 100)
			print("The simple GET with 100 requests working correctly")
		except Exception as e:	
			print("The simple GET with 100 requests not working correctly", e)
		self.recvd = 0

	def test_simple_get_with_1000_requests(self):
		print("\nSending multiple 1000 GET requests")
		for i in range(0, 100):
			Thread(target=self.multiple_get, args=(10, )).start()
		sleep(0.3)
		try:
			self.assertEqual(self.recvd, 1000)
			print("The simple GET with 1000 requests working correctly")
		except Exception as e:	
			print("The simple GET with 1000 requests not working correctly", e)
		#print(self.recvd)
	
	def test_not_found_get(self):
		print("\nSending simple GET request for non-existing file")
		response = requests.get('http://127.0.0.1:12345/not_exists.html')
		try:
			self.assertEqual(response.status_code, 404)
			print("The simple GET request for non-existing file working correctly")
		except Exception as e:	
			print("The simple GET request for non-existing file not working correctly", e)

	def test_get_bad_request(self):
		print("\nSending simple GET request with bad request URL")
		testerSocket = socket(AF_INET, SOCK_STREAM)
		testerSocket.connect(('', 12345))
		msg = headerMaker("GET", "index.html")
		testerSocket.sendall(msg.encode())
		response = testerSocket.recv(1024).decode()
		testerSocket.close()
		try:	
			self.assertEqual(int(response[9:12]), 400)
			print("The simple GET request for bad request URL working correctly")
		except Exception as e:
			print("The simple GET request for bad request URL not working correctly", e)

	

	
if __name__ == '__main__':
	unittest.main()
