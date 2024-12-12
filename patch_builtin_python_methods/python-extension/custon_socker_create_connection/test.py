import customsocket
customsocket.install_custom_create_connection()

# Now, all calls to socket.create_connection will use your custom function
import socket
socket.create_connection(('www.example.com', 80))