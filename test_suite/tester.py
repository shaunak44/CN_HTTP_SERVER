import requests
from threading import *
import unittest
from time import sleep
from socket import *
import argparse
import sys

port = "12345"


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


delete_file = open("delete_test.txt", "w+")

class GetRequestMaker(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(GetRequestMaker, self).__init__(*args, **kwargs)
		self.recvd = 0

	def test_a_simple_get(self):
		print("\nSending simple GET request")
		response = requests.get(f'http://127.0.0.1:{port}/index.html')
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple GET working correctly")
		except Exception as e:	
			print("The simple GET not working correctly", e)

	def test_a_simple_get_with_auth(self):	
		print("\nSending simple GET request with Valid Auth")
		response = requests.get(f'http://127.0.0.1:{port}/authorized.html', auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple GET working correctly with Valid Auth")
		except Exception as e:	
			print("The simple GET not working correctly with Valid Auth", e)
			
	def test_a_simple_get_with_inauth(self):	
		print("\nSending simple GET request with Invalid Auth")
		response = requests.get(f'http://127.0.0.1:{port}/authorized.html', auth=requests.auth.HTTPBasicAuth('temp', 'temp'))
		try:
			self.assertEqual(response.status_code, 401)
			print("The simple GET working correctly with Invalid Auth")
		except Exception as e:	
			print("The simple GET not working correctly with Invalid Auth", e)

	def test_a_simple_get_with_temp_redirect(self):	
		print("\nSending simple GET request for temporary redirect")
		response = requests.get(f'http://127.0.0.1:{port}/temp_redirect_from.html')
		try:
			self.assertEqual(str(response.history[0]), "<Response [307]>")
			print("The simple GET working correctly for temporary redirect")
		except Exception as e:	
			print("The simple GET not working correctly for temporary redirect", e)
	
	def test_a_simple_get_with_per_redirect(self):	
		print("\nSending simple GET request for permanent redirect")
		response = requests.get(f'http://127.0.0.1:{port}/per_redirect_from.html')
		try:
			self.assertEqual(str(response.history[0]), "<Response [301]>")
			print("The simple GET working correctly for permanent redirect")
		except Exception as e:	
			print("The simple GET not working correctly for permanent redirect", e)

	def test_a_simple_get_with_forbidden(self):
		print("\nSending simple GET request for forbidden file")
		response = requests.get(f'http://127.0.0.1:{port}/http.py')
		try:
			self.assertEqual(response.status_code, 403)
			print("The simple GET for forbidden file working correctly")
		except Exception as e:	
			print("The simple GET for forbidden file not working correctly", e)

	def multiple_get(self, num):
		for i in range (0, num):
			response = requests.get(f'http://127.0.0.1:{port}/index.html')
			if response.status_code == 200:
				self.recvd += 1
	
	def test_a_simple_get_with_25_requests(self):
		print("\nSending multiple 25 GET requests")
		for i in range(0, 5):
			Thread(target=self.multiple_get, args=(5, )).start()
		sleep(2)
		try:
			self.assertEqual(self.recvd, 25)
			print("The simple GET with 25 requests working correctly")
		except Exception as e:	
			print("The simple GET with 25 requests not working correctly", e)
		self.recvd = 0
		
	def test_a_not_found_get(self):
		print("\nSending simple GET request for non-existing file")
		response = requests.get(f'http://127.0.0.1:{port}/not_exists.html')
		try:
			self.assertEqual(response.status_code, 404)
			print("The simple GET request for non-existing file working correctly")
		except Exception as e:	
			print("The simple GET request for non-existing file not working correctly", e)

	def test_a_get_bad_request(self):
		print("\nSending simple GET request with bad request URL")
		testerSocket = socket(AF_INET, SOCK_STREAM)
		testerSocket.connect(('', int(port)))
		msg = headerMaker("GET", "index.html")
		testerSocket.sendall(msg.encode())
		response = testerSocket.recv(1024).decode()
		testerSocket.close()
		try:	
			self.assertEqual(int(response[9:12]), 400)
			print("The simple GET request for bad request URL working correctly")
		except Exception as e:
			print("The simple GET request for bad request URL not working correctly", e)

	def test_a_get_timeout_request(self):
		print("\nSending simple GET request with bad request URL")
		testerSocket = socket(AF_INET, SOCK_STREAM)
		testerSocket.connect(('', int(port)))
		msg = headerMaker("GET", "index.html")
		sleep(1.5)
		testerSocket.sendall(msg.encode())
		response = testerSocket.recv(1024).decode()
		testerSocket.close()
		try:	
			self.assertEqual(int(response[9:12]), 408)
			print("The simple GET request for timeout working correctly")
		except Exception as e:
			print("The simple GET request for timeout not working correctly", e)
	
	def test_a_simple_get_with_cookies(self):
		print("\nSending simple GET request with Cookies")
		response = requests.get(f'http://127.0.0.1:{port}/index.html')
		try:
			self.assertTrue("TestCookie" in response.headers["Set-Cookie"] )
			print("The simple GET working correctly")
		except Exception as e:	
			print("The simple GET not working correctly", e)

	def test_a_simple_get_with_if_range_single_part_partial_content(self):
		print("\nSending simple GET request with If Range Single part for partial content")
		response = requests.get(f'http://127.0.0.1:{port}/index.html', headers = {"If-Range": "Wed Nov 11 12:08:14 2021", "Range":"bytes=100-500"})
		try:
			self.assertEqual(response.status_code, 206)
			print("The simple GET with If Range Single part for partial content working correctly")
		except Exception as e:	
			print("The simple GET with If Range Single part for partial content not working correctly", e)

	def test_a_simple_get_with_if_range_multi_part_partial_content(self):
		print("\nSending simple GET request with If Range multipart")
		response = requests.get(f'http://127.0.0.1:{port}/index.html', headers = { "Range":"bytes=100-500, 700-900, 1300-1600", "If-Range": "Wed Nov 11 12:08:14 2021",})
		try:
			self.assertEqual(response.status_code, 206)
			print("The simple GET with If Range multipart for partial content working correctly")
		except Exception as e:	
			print("The simple GET with If Range multipart for partial content not working correctly", e)

	def test_a_simple_get_with_if_range_single_part_full_content(self):
		print("\nSending simple GET request with If Range Single part full content")
		response = requests.get(f'http://127.0.0.1:{port}/index.html', headers = {"If-Range": "Wed Nov 11 12:08:14 2019", "Range":"bytes=100-500"})
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple GET with If Range Single part full content working correctly")
		except Exception as e:	
			print("The simple GET with If Range Single part  full content not working correctly", e)

	def test_a_simple_get_with_if_range_multi_part_full_content(self):
		print("\nSending simple GET request with If Range multipart full content")
		response = requests.get(f'http://127.0.0.1:{port}/index.html', headers = {"If-Range": "Wed Nov 11 12:08:14 2019", "Range":"bytes=100-500, 700-900, 1300-1600"})
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple GET with If Range multipart full content working correctly")
		except Exception as e:	
			print("The simple GET with If Range multipart full content not working correctly", e)

	def test_a_simple_get_with_if_range_not_satisfiable(self):
		print("\nSending simple GET request with If Range not satisfiable")
		response = requests.get(f'http://127.0.0.1:{port}/index.html', headers = {"If-Range": "Wed Nov 11 12:08:14 2021", "Range":"bytes=100-"})
		try:
			self.assertEqual(response.status_code, 416)
			print("The simple GET with If Range Single part not satisfiable working correctly")
		except Exception as e:	
			print("The simple GET with If Range Single part not satisfiable not working correctly", e)

	def test_a_simple_get_if_modified_since_modified(self):
		print("\nSending simple GET request If Modified Since Modified")
		response = requests.get(f'http://127.0.0.1:{port}/index.html', headers = {"If-Modified-Since":"Wed Nov 11 12:07:14 2019"})
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple GET with If modified since - modified working correctly")
		except Exception as e:	
			print("The simple GET with If modified since - modified not working correctly", e)

	def test_a_simple_get_if_modified_since_not_modified(self):
		print("\nSending simple GET request If Modified Since not Modified")
		response = requests.get(f'http://127.0.0.1:{port}/index.html', headers = {"If-Modified-Since":"Wed Nov 11 12:07:14 2021"})
		try:
			self.assertEqual(response.status_code, 304)
			print("The simple GET with If modified since - not modified working correctly")
		except Exception as e:	
			print("The simple GET with If modified since - not modified not working correctly", e)

	def test_b_simple_post(self):
		print("\nSending simple POST request")
		response = requests.post(f'http://127.0.0.1:{port}/index.html', data="Test data for Simple Post")
		try:
			self.assertEqual(response.status_code, 204)
			print("The simple POST working correctly")
		except Exception as e:	
			print("The simple POST not working correctly", e)	

	def test_b_post_bad_request(self):
		print("\nSending simple POST request with bad request URL")
		testerSocket = socket(AF_INET, SOCK_STREAM)
		testerSocket.connect(('', int(port)))
		msg = headerMaker("POST", "index.html")
		testerSocket.sendall(msg.encode())
		response = testerSocket.recv(1024).decode()
		testerSocket.close()
		try:
			#print(response)
			self.assertEqual(int(response[9:12]), 400)
			print("The simple POST request for bad request URL working correctly")
		except Exception as e:
			print("The simple POST request for bad request URL not working correctly", e)
	
	def multiple_post(self, num):
		for i in range (0, num):
			response = requests.post(f'http://127.0.0.1:{port}/index.html', data="Test data for multiple post")
			if response.status_code == 204:
				self.recvd += 1
	
	def test_b_simple_post_with_25_requests(self):
		print("\nSending multiple 25 POST requests")
		for i in range(0, 5):
			Thread(target=self.multiple_post, args=(5, )).start()
		sleep(1)
		try:
			self.assertEqual(self.recvd, 25)
			print("The simple POST with 25 requests working correctly")
		except Exception as e:	
			print("The simple POST with 25 requests not working correctly", e)
		self.recvd = 0

#here replace filename with some non_existing fileName
	def test_c_simple_put_non_existing_valid_auth(self):
		print("\nSending simple PUT request for non existing file with valid auth")
		response = requests.put(f'http://127.0.0.1:{port}/put_test.txt', data="Test data for Simple PUT", auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
		try:
			self.assertEqual(response.status_code, 201)
			print("The simple PUT request for non existing file with valid auth working correctly")
		except Exception as e:	
			print("The simple PUT request for non existing file with valid auth not working correctly", e)

	def test_c_simple_put_non_existing_invalid_auth(self):
		print("\nSending simple PUT request for non existing file with invalid auth")
		response = requests.put(f'http://127.0.0.1:{port}/put_test.txt', data="Test data for Simple PUT", auth=requests.auth.HTTPBasicAuth('temp', 'temp'))
		try:
			self.assertEqual(response.status_code, 401)
			print("The simple PUT request for non existing file with invalid auth working correctly")
		except Exception as e:	
			print("The simple PUT request for non existing file with invalid auth not working correctly", e)

	def test_ctest_ctest_c_simple_post_with_forbidden(self):
		print("\nSending simple POST request for forbidden file")
		response = requests.post(f'http://127.0.0.1:{port}/http.py', data="Test data for POST")
		try:
			self.assertEqual(response.status_code, 403)
			print("The simple POST for forbidden file working correctly")
		except Exception as e:	
			print("The simple POST for forbidden file not working correctly", e)

	def test_c_simple_put_existing_valid_auth(self):
		print("\nSending simple PUT request for existing file with valid auth")
		response = requests.put(f'http://127.0.0.1:{port}/put_test.txt', data="Test data for Simple PUT", auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
		try:
			self.assertEqual(response.status_code, 204)
			print("The simple PUT request for existing file with valid auth working correctly")
		except Exception as e:	
			print("The simple PUT request for existing file with valid auth not working correctly", e)

	def test_c_simple_put_existing_invalid_auth(self):
		print("\nSending simple PUT request for existing file with invalid auth")
		response = requests.put(f'http://127.0.0.1:{port}/put_test.txt', data="Test data for Simple PUT", auth=requests.auth.HTTPBasicAuth('temp', 'temo'))
		try:
			self.assertEqual(response.status_code, 401)
			print("The simple PUT request for existing file with invalid auth working correctly")
		except Exception as e:	
			print("The simple PUT request for existing file with invalid auth not working correctly", e)

	def multiple_put(self, num):
		for i in range (0, num):
			response = requests.put(f'http://127.0.0.1:{port}/test_put.txt', data="Test data for multiple PUT", auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
			if response.status_code == 204:
				self.recvd += 1

	def test_c_simple_put_with_25_requests(self):
		print("\nSending multiple 25 PUT requests")
		for i in range(0, 5):
			Thread(target=self.multiple_put, args=(5, )).start()
		sleep(1)
		try:
			self.assertEqual(self.recvd, 25)
			print("The simple PUT with 25 requests working correctly")
		except Exception as e:	
			print("The simple PUT with 25 requests not working correctly", e)
		self.recvd = 0

	def test_c_put_bad_request(self):
		print("\nSending simple PUT request with bad request URL")
		testerSocket = socket(AF_INET, SOCK_STREAM)
		testerSocket.connect(('', int(port)))
		msg = headerMaker("PUT", "test_put.txt")
		testerSocket.sendall(msg.encode())
		response = testerSocket.recv(1024).decode()
		testerSocket.close()
		try:
			#print(response)
			self.assertEqual(int(response[9:12]), 401)
			print("The simple PUT request for bad request URL working correctly")
		except Exception as e:
			print("The simple PUT request for bad request URL not working correctly", e)

	def test_c_simple_put_with_forbidden(self):
		print("\nSending simple PUT request for forbidden file")
		response = requests.put(f'http://127.0.0.1:{port}/http.py')
		try:
			self.assertEqual(response.status_code, 403)
			print("The simple PUT for forbidden file working correctly")
		except Exception as e:	
			print("The simple PUT for forbidden file not working correctly", e)

	def test_c_simple_head(self):
		print("\nSending simple HEAD request")
		response = requests.head(f'http://127.0.0.1:{port}/index.html')
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple HEAD working correctly")
		except Exception as e:	
			print("The simple HEAD not working correctly", e)

	def test_d_simple_head_with_auth(self):	
		print("\nSending simple HEAD request with Valid Auth")
		response = requests.head(f'http://127.0.0.1:{port}/authorized.html', auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
		try:
			self.assertEqual(response.status_code, 200)
			print("The simple HEAD working correctly with Valid Auth")
		except Exception as e:	
			print("The simple HEAD not working correctly with Valid Auth", e)
			
	def test_d_simple_head_with_inauth(self):	
		print("\nSending simple HEAD request with Invalid Auth")
		response = requests.head(f'http://127.0.0.1:{port}/authorized.html', auth=requests.auth.HTTPBasicAuth('temp', 'temp'))
		try:
			self.assertEqual(response.status_code, 401)
			print("The simple HEAD working correctly with Invalid Auth")
		except Exception as e:	
			print("The simple HEAD not working correctly with Invalid Auth", e)

	def test_d_simple_head_with_temp_redirect(self):	
		print("\nSending simple HEAD request for temporary redirect")
		response = requests.head(f'http://127.0.0.1:{port}/temp_redirect_from.html')
		#print(response.status_code)
		try:
			self.assertEqual(response.status_code, 307)
			print("The simple HEAD working correctly for temporary redirect")
		except Exception as e:	
			print("The simple HEAD not working correctly for temporary redirect", e)
	
	def test_d_simple_head_with_per_redirect(self):	
		print("\nSending simple HEAD request for permanent redirect")
		response = requests.head(f'http://127.0.0.1:{port}/per_redirect_from.html')
		#print(response.status_code)
		try:
			self.assertEqual(response.status_code, 301)
			print("The simple HEAD working correctly for permanent redirect")
		except Exception as e:	
			print("The simple HEAD not working correctly for permanent redirect", e)

	def multiple_head(self, num):
		for i in range (0, num):
			response = requests.head(f'http://127.0.0.1:{port}/index.html')
			if response.status_code == 200:
				self.recvd += 1
	
	def test_d_simple_head_with_25_requests(self):
		print("\nSending multiple 25 HEAD requests")
		for i in range(0, 5):
			Thread(target=self.multiple_head, args=(5, )).start()
		sleep(1)
		try:
			self.assertEqual(self.recvd, 25)
			print("The simple HEAD with 25 requests working correctly")
		except Exception as e:	
			print("The simple HEAD with 25 requests not working correctly", e)
		self.recvd = 0
		
	def test_d_not_found_head(self):
		print("\nSending simple HEAD request for non-existing file")
		response = requests.get(f'http://127.0.0.1:{port}/not_exists.html')
		try:
			self.assertEqual(response.status_code, 404)
			print("The simple HEAD request for non-existing file working correctly")
		except Exception as e:	
			print("The simple HEAD request for non-existing file not working correctly", e)

	def test_d_head_bad_request(self):
		print("\nSending simple HEAD request with bad request URL")
		testerSocket = socket(AF_INET, SOCK_STREAM)
		testerSocket.connect(('', int(port)))
		msg = headerMaker("HEAD", "index.html")
		testerSocket.sendall(msg.encode())
		response = testerSocket.recv(1024).decode()
		testerSocket.close()
		try:	
			self.assertEqual(int(response[9:12]), 400)
			print("The simple HEAD request for bad request URL working correctly")
		except Exception as e:
			print("The simple HEAD request for bad request URL not working correctly", e)

	def test_e_simple_delete_non_existing_with_valid_auth(self):
		print("\nSending simple DELETE request for non existing file with valid auth")
		response = requests.delete(f'http://127.0.0.1:{port}/delete_test.txt', auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
		try:
			self.assertEqual(response.status_code, 404)
			print("The simple DELETE request for non existing file working correctly")
		except Exception as e:	
			print("The simple DELETE request for non existing file not working correctly", e)

	def test_e_simple_delete_non_existing_auth(self):
		print("\nSending simple DELETE request for non existing file with invalid auth")
		response = requests.delete(f'http://127.0.0.1:{port}/delete_test.txt', auth=requests.auth.HTTPBasicAuth('tmep', 'temp'))
		try:
			self.assertEqual(response.status_code, 401)
			print("The simple DELETE request for non existing file working correctly")
		except Exception as e:	
			print("The simple DELETE request for non existing file not working correctly", e)

	def test_e_simple_delete_existing_with_auth(self):
		print("\nSending simple DELETE request for existing file with valid auth")
		response = requests.delete(f'http://127.0.0.1:{port}/delete_test.txt', auth=requests.auth.HTTPBasicAuth('shaunak', 'shaunak'))
		try:
			self.assertEqual(response.status_code, 204)
			print("The simple DELETE request for existing file working correctly")
		except Exception as e:	
			print("The simple DELETE request for existing file not working correctly", e)		

	def test_e_simple_delete_existing_invalid_auth(self):
		print("\nSending simple DELETE request for existing file with invalid auth")
		response = requests.delete(f'http://127.0.0.1:{port}/delete_test.txt', auth=requests.auth.HTTPBasicAuth('temp', 'temp'))
		try:
			self.assertEqual(response.status_code, 401)
			print("The simple DELETE request for existing file working correctly")
		except Exception as e:	
			print("The simple DELETE request for existing file not working correctly", e)	

	def test_e_delete_bad_request_invalid_auth(self):
		print("\nSending simple DELETE request with bad request URL with invalid auth")
		testerSocket = socket(AF_INET, SOCK_STREAM)
		testerSocket.connect(('', int(port)))
		msg = headerMaker("DELETE", "test_put.txt")
		testerSocket.sendall(msg.encode())
		response = testerSocket.recv(1024).decode()
		testerSocket.close()
		try:
			#print(response)
			self.assertEqual(int(response[9:12]), 401)
			print("The simple DELETE request for bad request URL with invalid auth working correctly")
		except Exception as e:
			print("The simple DELETE request for bad request URL with invalid auth not working correctly", e)
	


if __name__ == '__main__':
	unittest.main()
