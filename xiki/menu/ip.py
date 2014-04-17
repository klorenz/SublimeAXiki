def menu():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("gmail.com",80))
		return str(s.getsockname()[0])
		s.close()
	except:
		import socket
		return str(socket.gethostbyname(socket.gethostname()))