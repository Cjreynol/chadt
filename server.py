from threading import Thread
from socket import socket
from time import sleep
import logging as log


class Server(object):
    
    def __init__(self, port = 36000):
        self.port = port
        self.clients = dict()
        self.listener = self.create_listen_socket(("localhost", self.port))

        self.running = False
        self.receiver_thread = create_thread(self.listen)
        self.relay_thread = create_thread(self.relay_messages)

        log.info("Server created with port {}.".format(self.port))

    def start_server(self):
        self.running = True
        self.receiver_thread.start()
        self.relay_thread.start()

        log.info("Server started.")

    def relay_messages(self):
        log.info("Message relaying started.")
        while self.running:
             for address, client in self.clients.items():
                if client.complete:
                    try:
                        message = client.get_message_from()
                        log.debug("Received message from {}: {}".format(address, message))
                        self.relay_message(message, address)

                    except BlockingIOError:
                        log.debug("No message from {}.".format(address))

            sleep(1)

    

    def relay_message(self, message, sender):
        for address, client in self.clients.items():
            if sender != address:
                client.send_message_to(message)
                log.debug("Sent message to {}.".format(address))

    def listen(self):
        log.info("Connection listening started.")
        while self.running:
            connection = self.listener.accept()
            log.info("New Connection.")
            new_socket, address = (connection[0], connection[1])

            if address not in self.clients:
                self.clients[address] = ClientConnection(address, new_socket)
                log.debug("Connection is new client at address {}.".format(address))

            else:
                new_socket.setblocking(False)
                self.clients[address].client_transmitter(new_socket)
                self.clients[address].complete = True
                log.debug("Connection is existing client at address {}.".format(address))

    def create_listen_socket(self, address):
        s = socket()
        s.bind(address)
        s.listen()
        return s
    
    def create_thread(self, target_func):
        return Thread(target = target_func)
    

class ClientConnection(object):

    MESSAGE_BUFFER_SIZE = 4096

    def __init__(self, address, receiver_socket, transmitter_socket=None):
        self.address = address
        self.client_receiver = receiver_socket
        self.client_transmitter = transmitter_socket
        self.complete = False

    def get_message_from(self):
        return self.client_transmitter.recv(ClientConnection.MESSAGE_BUFFER_SIZE)

    def send_message_to(self, message):
        self.client_receiver.sendall(message)


