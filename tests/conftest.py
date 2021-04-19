import pytest

import threading
from server import configure_connection
from client import Client

HOST = '127.0.0.1'
PORT = 8080


@pytest.fixture(autouse=True)
def server():
    thread = threading.Thread(target=configure_connection, args=(HOST, PORT))
    thread.start()
    yield thread


@pytest.fixture
def client():
    with Client(HOST, PORT) as client:
        yield client
