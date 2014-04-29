
def menu():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("gmail.com", 80))
        result = str(s.getsockname()[0])
        s.close()
        return result
    except:
        return str(socket.gethostbyname(socket.gethostname()))
