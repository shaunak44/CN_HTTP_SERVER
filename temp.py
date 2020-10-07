from socket import *
import _thread
import sys

clients = {}

TotalUser = 0
portNumber = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', portNumber))
serverSocket.listen(20)
print("*****Chat server started*****")

def client_thread(connection):
    user = connection.recv(1024)
    user = str(user.decode())
    clients[user] = connection
    welcome_msg = "Welcome "+ user + " to the ChatRoom" 
    connection.send(welcome_msg.encode())
    joined_msg = user + " joined the chat"
    for i in clients:
        if(user != i):
            clients[i].sendall(joined_msg.encode())
    while True:
        try:
            data = connection.recv(1024)
            reply = str(data.decode())
            #print(reply)
            sender, msg = reply.split(":")
            other_msg = sender + " says: " + msg
            for i in clients:
                if(i != sender):
                    clients[i].sendall(other_msg.encode())
                else:
                    your_msg = "You: "+ msg
                    clients[i].sendall(your_msg.encode())
        except:
            for i in clients:
                if(i != sender):
                    clients[i].sendall((sender + " left the chat").encode())
            del clients[sender]
            break

    connection.close()


while True:
    try:
        clientSocket, address = serverSocket.accept()
        print("Connected to", address)
        _thread.start_new_thread(client_thread, (clientSocket, ))
        TotalUser += 1
        print("Thread", TotalUser)
    except:
        print("\n*****Chat server stopped*****")
        break

serverSocket.close()
