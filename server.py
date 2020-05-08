"""
Серверное приложение для соединений
"""

import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                for client in self.server.clients:
                    if client.login == decoded.replace("login:", "").replace("\r\n", ""):
                        print(f"huy {client.login}")
                        self.transport.close()
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                self.transport.write(
                    f"Привет, {self.login}!".encode()
                )
                self.send_history()
        else:
            self.send_message(decoded)

    def send_history(self):
        if len(self.server.history) > 0:
            perenos = "\n"
            for mess in self.server.history:
                self.transport.write(mess)
                self.transport.write(perenos.encode())

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        if len(self.server.history)==0:
            self.server.first_message=encoded
        if len(self.server.history) > 9:
            self.server.history.remove(self.server.first_message)
            self.server.first_message=self.server.history[0]
        self.server.history.append(encoded)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list
    first_message: str

    def __init__(self):
        self.clients = []
        self.history = []
        self.first_message=None

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
