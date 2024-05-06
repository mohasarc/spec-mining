import socket
import socketextension  # Importing the module initializes the method attachment

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.send_event()  # This will print the socket object's memory address