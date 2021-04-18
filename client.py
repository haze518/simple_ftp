import socket
import os

import codes


class Client:
    def __init__(self, host, port):
        self.user_pi = self.connect_server(host, port)
        self.data_connection = False
        self.buffers_size = 1024

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.data_connection.close()
        self.user_pi.close()

    def create_data_connection(self, host, port):
        self.data_connection = self.connect_server(host, port)

    def parse_data_connection_path(self, path):
        host_port = path.split(',')
        host = '.'.join(host_port[:4])
        port = (int(host_port[4])<<8) + int(host_port[5])
        return host, port

    def user_pi_command(self, msg):
        self.user_pi.send(msg)
        return self.user_pi.recv(self.buffers_size).decode('utf-8')

    def dtf_command(self, msg):
        self.user_pi.send(msg)
        return self.data_connection.recv(self.buffers_size).decode('utf-8')

    def retrieve(self, from_file, to_file):
        if self.data_connection:
            self.user_pi.send(b'RETR ' + from_file)
            with open(to_file, 'wb') as f:
                while True:
                    data = self.data_connection.recv(self.buffers_size)
                    stop_success = codes.REQUESTED_ACTION_COMPLETED
                    stop_fail = codes.REQUESTED_ACTION_NOT_TAKEN
                    if data in (stop_success, stop_fail) or not data:
                        break
                    f.write(data)
        else:
            raise ValueError('Отсутствует соединения с сервером данных.')

    def connect_server(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        return s

if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 8080
    with Client(HOST, PORT) as client:
        user = client.user_pi_command(b'USER ash')
        print(user)

        data_address = client.user_pi_command(b'PASV')
        print(data_address)
        data_host, data_port = client.parse_data_connection_path(data_address)
        print(data_host, data_port)
        client.create_data_connection(data_host, data_port)

        pwd = client.dtf_command(b'PWD')
        print(pwd)

        l = client.dtf_command(b'LIST ' + bytes(pwd, encoding='utf-8'))
        print(l)

        directory  = client.dtf_command(b'MKD hz')
        print(directory)

        drop_directory = client.dtf_command(b'RMD hz')
        print(drop_directory)

        with open('random_server_file.txt', 'wb') as f:
            f.write(os.urandom(2048))

        client.retrieve(b'random_server_file.txt', b'new_file.txt')
        with open('new_file.txt', 'rb') as f:
            second = f.read()

        with open('random_server_file.txt', 'rb') as f:
            first = f.read()
        print(second == first)
        client.dtf_command(b'DELE random_server_file.txt')
        client.dtf_command(b'DELE new_file.txt')

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect(SERVER_ADDERSS)
# s.send(b'USER ash')
# data = s.recv(1024).decode('utf-8')
# print(data)

# s.send(b'PASV')
# data = s.recv(1024).decode('utf-8')
# print(data)

# host_port = data.split(',')
# print(host_port)
# host = '.'.join(host_port[:4])
# port = (int(host_port[4])<<8) + int(host_port[5])
# host = '.'.join(host_port[:4])


# s.send(b'PWD')
# data = new_s.recv(1024).decode('utf-8')
# print(data)

# print('list' + data)

# s.send(b'LIST ' + bytes(data, encoding='utf-8'))
# data = new_s.recv(1024).decode('utf-8')
# print(data)

# s.send(b'MKD ' + b'YOOO')
# data = new_s.recv(1024).decode('utf-8')
# print(data)

# s.send(b'RMD ' + b'YOOO')
# data = new_s.recv(1024).decode('utf-8')
# print(data)

# s.send(b'RETR asd.txt')
# with open('ff.txt', 'w') as f:
#     while True:
#         data = new_s.recv(1024).decode('utf-8')
#         stop = REQUESTED_ACTION_COMPLETED
#         if data == stop or not data:
#             break
#         f.write(data)
