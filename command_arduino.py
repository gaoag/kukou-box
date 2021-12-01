from serial import Serial
import socket

class BasicArduinoOutputModule:
    def __init__(self, port, baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def init_connection(self):
        self.ser = Serial(self.port, self.baudrate, timeout=2.5)

    def send_message(self, message, format):
        self.ser.write(message.encode(format))
        self.ser.flush()


class BasicArduinoOutputModuleTCPSerial:
    def __init__(self, host='localhost', port=13000, baudrate=9600):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.s.connect((self.host, self.port))

    def send_message(self, message, format):

        self.s.sendall(message.encode(format))
        data = self.s.recv(1024)
        print('received ' + repr(data))


    # def init_connection(self):
    #     self.ser = Serial(self.port, self.baudrate, timeout=0)

    # def send_message(self, message):
    #     self.ser.write(message.encode('UTF-8'))
