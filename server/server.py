import logging as log

from chadt.connection_handler import ConnectionHandler
from chadt.constants import DEFAULT_USERNAME_BASE, SERVER_NAME
from chadt.message import Message
from chadt.message_handler import MessageHandler
from chadt.message_type import MessageType
from chadt.system_message import SystemMessage

from lib.observed_list import ObservedList

from server.listener import Listener
from server.message_relayer import MessageRelayer


class Server(MessageHandler):
    
    def __init__(self, port, system_message_queue):
        super().__init__(MessageType)

        self.clients = dict()
        self.message_out_queue = []
        self.system_message_queue = system_message_queue

        self.connections = ObservedList()
        self.temp_id_counter = 0

        self.listener = Listener(port, self.connections)
        self.message_relayer = MessageRelayer(self.message_out_queue, self.clients)

        log.info("Server created listening at port {}.".format(port))

    def start_server(self):
        self.listener.start()
        self.message_relayer.start()
        super().start()

        self.connections.add_observer(self._add_new_client)
        log.info("Server started.")

    def stop_server(self):
        self.listener.stop()
        self.message_relayer.stop()
        super().stop()
        log.info("Server stopped.")

    def shutdown_server(self):
        self.listener.shutdown()
        self.message_relayer.shutdown()

        disconnect_message = Message.construct_disconnect("", SERVER_NAME)
        for client_connection in self.clients.values():
            client_connection.shutdown(disconnect_message)
        super().shutdown()
        log.info("Server shut down.")
    
    def handle_text(self, message):
        system_message = SystemMessage.construct_text(message.get_display_string())
        self.system_message_queue.append(system_message)
        self.message_out_queue.append(message)

    def handle_disconnect(self, message):
        username = message.sender
        self.clients[username].shutdown()
        del self.clients[username]
        self._send_user_disconnect(username)

    def handle_username_request(self, message):
        username = message.text
        message_constructor = Message.construct_username_accepted
        recipient = username

        if username not in self.clients and self.is_username_valid_length(username):
            self.clients[username] = self.clients.pop(message.sender)
            self.clients[username].username = username
            self._send_username_change(message.sender, username)
        else:
            message_constructor = Message.construct_username_rejected
            recipient = message.sender

        response_message = message_constructor(username, SERVER_NAME, recipient)
        self.clients[recipient].add_message_to_out_queue(response_message)

    def _get_next_temp_id(self):
        username = DEFAULT_USERNAME_BASE + str(self.temp_id_counter)
        self.temp_id_counter += 1
        return username

    def _add_new_client(self, connection_list):
        connection = connection_list.pop(0)
        username = self._get_next_temp_id()
        current_users = ",".join(self.clients.keys())

        self.clients[username] = ConnectionHandler(username, connection, self.message_processing_queue, is_server_connection = True)

        temp_id_message = Message.construct_temp_username_assigned(username, SERVER_NAME, username)
        self.clients[username].add_message_to_out_queue(temp_id_message)

        if current_users != "":     # first user connection, no previous users
            previous_users_message = Message.construct_list_of_users(current_users, SERVER_NAME, username)
            self.clients[username].add_message_to_out_queue(previous_users_message)

        self.clients[username].start()
        self._send_user_connect(username)

    def _send_username_change(self, old_username, new_username):
        text = old_username + "," + new_username
        username_change_message = Message.construct_user_name_change(text, SERVER_NAME)
        self._send_system_message_user_update(username_change_message)
        self.message_out_queue.append(username_change_message)

    def _send_user_connect(self, username):
        user_connect_message = Message.construct_user_connect(username, SERVER_NAME)
        self._send_system_message_user_update(user_connect_message)
        self.message_out_queue.append(user_connect_message)

    def _send_user_disconnect(self, username):
        user_disconnect_message = Message.construct_user_disconnect(username, SERVER_NAME)
        self._send_system_message_user_update(user_disconnect_message)
        self.message_out_queue.append(user_disconnect_message)

    def _send_system_message_user_update(self, message):
        system_message = SystemMessage.construct_user_list_update(message.get_display_string())
        self.system_message_queue.append(system_message)
