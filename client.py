import socket

msgFromClient       = '{"device":"Device1","latitude":45.2,"longitude":1.2}'
bytesToSend         = str.encode(msgFromClient)
serverAddressPort   = ("127.0.0.1", 50120)
bufferSize          = 1024
# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
# Send to server using created UDP socket
UDPClientSocket.sendto(bytesToSend, serverAddressPort)
print("Message Sent!")
msgFromServer = UDPClientSocket.recvfrom(bufferSize)
msg = "Message from Server {}".format(msgFromServer[0])
print(msg)