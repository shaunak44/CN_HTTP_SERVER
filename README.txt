Project Name: HTTP Server

Developed by:
1) Shaunak Mahajan (111803072)
2) Vedant Lokhande (111803070)

HTTP Server
This is the HTTP Server implementation with 5 methods: GET, POST, PUT, DELETE and HEAD

Program Structure:
HTTP_SERVER
    |-logs
    |   |-access.log
    |   |-error.log
    |   |-debug.log
    |   |-post.log
    |-root
    |   |-*.html
    |-test_suite
    |   |-tester.py
    |-http_server.py
    |-server.conf
    |-cookies.txt
    |-README.txt

Requirements:
1) python3
2) wsgiref (time formatter module)
3) mimetypes
4) requests (for HTTP requests)

Usage:
Server:
    Start: python3 http_server.py [Port Number]
    Stop: Press Control+C to exit
Tester:
    python3 tester.py
