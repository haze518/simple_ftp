import socket
import shutil
import os
from functools import wraps

import codes


def configure_connection(host, port):
    """Создание соединения."""
    print(f'run server on {host}:{port}')
    sock = bind_socket(host, port)
    while True:
        try:
            conn, addr = sock.accept()
            print(f'user: {addr}, connected')
            FTPServer(conn, addr).run_server()
        except KeyboardInterrupt:
            sock.close()
            break


def bind_socket(host, port):
    """Привязать слушающий сокет к ip и порту."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()
    return sock


class FTPServer:

    def __init__(
        self,
        connection,
        address,
    ):
        self.connection = connection
        self.address = address
        self.is_logged = False
        self.pasv = False
        self.data_connection = False
        self.buffer_size = 1024

    def run_server(self):
        while True:
            data = self.connection.recv(self.buffer_size)
            if not data:
                break
            decoded = data.decode('utf-8').split(' ', 1)
            command = decoded[0]
            arg = decoded[1].lstrip(' ') if len(decoded) > 1 else None
            if not self.command_exists(command):
                self.send_message(codes.SYNTAX_ERROR)
            else:
                ftp_command = getattr(self, command)
                ftp_command(arg)
        self.data_connection.close()

    def argument_checker(check, message):
        """Проверка аргументов класса."""
        def decorate(func):
            @wraps(func)
            def wrap(self, *args, **kwargs):
                res = None
                if getattr(self, check, None):
                    res = func(self, *args, **kwargs)
                else:
                    self.send_message(message)
                return res
            return wrap
        return decorate

    def send_message(self, msg):
        if not isinstance(msg, bytes):
            msg = bytes(msg, encoding='utf-8')
        self.connection.send(msg)

    def command_exists(self, command):
        return bool(getattr(self, command, None))

    def USER(self, username):
        """Проверка пользователя."""
        if username:
            self.send_message(codes.LOGGED_IN)
            self.is_logged = True
        else:
            self.send_message(codes.NOT_LOGGED_IN)

    @argument_checker('is_logged', codes.NOT_LOGGED_IN)
    def PASV(self, *args):
        """Перевести сервер в пассивный режим."""
        sock = bind_socket(HOST, 0)
        port = sock.getsockname()[1]
        hbytes = HOST.split('.')
        pbytes = [repr(port//256), repr(port%256)]
        port_bytes = hbytes + pbytes
        cmd = ','.join(port_bytes)
        self.connection.sendall(bytes(cmd, 'utf-8'))
        self.data_connection, _ = sock.accept()
        self.pasv = True

    @argument_checker('pasv', codes.CANT_OPEN_DATA_CONNECTION)
    @argument_checker('is_logged', codes.NOT_LOGGED_IN)
    def PWD(self, *args):
        """Показать путь."""
        path = os.getcwdb()
        self.data_connection.send(path)

    @argument_checker('pasv', codes.CANT_OPEN_DATA_CONNECTION)
    @argument_checker('is_logged', codes.NOT_LOGGED_IN)
    def LIST(self, path):

        """Вывести список файлов."""
        if os.path.exists(path):
            list_dir = '\n'.join(os.listdir(path))
            self.data_connection.send(bytes(list_dir, encoding='utf-8'))
        else:
            self.data_connection.send(codes.REQUESTED_ACTION_NOT_TAKEN)

    @argument_checker('pasv', codes.CANT_OPEN_DATA_CONNECTION)
    @argument_checker('is_logged', codes.NOT_LOGGED_IN)
    def MKD(self, dirname):
        """Создание дирректории."""
        os.makedirs(dirname)
        msg = codes.PATHNAME_CREATED.decode('utf-8').replace("PATHNAME", f"{dirname}")
        self.data_connection.send(bytes(msg, encoding='utf-8'))

    @argument_checker('pasv', codes.CANT_OPEN_DATA_CONNECTION)
    @argument_checker('is_logged', codes.NOT_LOGGED_IN)
    def DELE(self, filename):
        """Удалить файл."""
        path = os.path.join(os.getcwd(), filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                self.data_connection.send(codes.REQUESTED_ACTION_COMPLETED)
            except OSError:
                self.data_connection.send(codes.REQUEST_FILE_ACTION_ABORTED)
        else:
            self.data_connection.send(codes.REQUESTED_ACTION_NOT_TAKEN)

    @argument_checker('pasv', codes.CANT_OPEN_DATA_CONNECTION)
    @argument_checker('is_logged', codes.NOT_LOGGED_IN)
    def RMD(self, dirname):
        """Удалить папку."""
        path = os.path.join(os.getcwd(), dirname)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                self.data_connection.send(codes.REQUESTED_ACTION_COMPLETED)
            except OSError:
                self.data_connection.send(codes.REQUEST_FILE_ACTION_ABORTED)
        else:
            self.data_connection.send(codes.REQUESTED_ACTION_NOT_TAKEN)

    @argument_checker('pasv', codes.CANT_OPEN_DATA_CONNECTION)
    @argument_checker('is_logged', codes.NOT_LOGGED_IN)
    def RETR(self, pathname):
        """Отправка файла."""
        path = os.path.join(os.getcwd(), pathname)
        if os.path.exists(path):
            with open(pathname, 'rb') as f:
                while True:
                    chunk = f.read(self.buffer_size)
                    if not chunk:
                        break
                    self.data_connection.send(chunk)
                self.data_connection.send(codes.REQUESTED_ACTION_COMPLETED)
        else:
            self.data_connection.send(codes.REQUESTED_ACTION_NOT_TAKEN)


if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 8080
    configure_connection(HOST, PORT)
