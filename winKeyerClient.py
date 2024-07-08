import socket

server_host = '127.0.0.1'
server_port = 7373

def send_message(host, port, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(message.encode('ascii'))
            print(f"Sent: {message}")
    except Exception as e:
        print(f"Failed to send message: {e}")

while True:
    message = input("Enter message to send (or 'quit' to exit): ")
    if message.lower() == 'quit':
        break
    message = message.replace("&",(chr(27)+"BK"))
    send_message(server_host, server_port, message)
