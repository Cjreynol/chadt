from socket import socket, SO_REUSEADDR, SOL_SOCKET
from struct import pack, unpack

from chadt.chadt_exceptions import ZeroLengthMessageException
from chadt.connection_status import ConnectionStatus
from chadt.constants import RECIPIENT_MAX_LENGTH, SENDER_MAX_LENGTH, SOCKET_TIMEOUT
from chadt.message import Message


class Connection:
    """Wraps a socket with Message handling logic and convenience methods.

    The constructor arguments determine the connection type:  new connection, 
    existing connection, or listening connection.

    """

    def __init__(self, port = None, server_host = None, connected_socket = None):
        self.port = port
        self.server_host = server_host

        self.socket = connected_socket
        if self.socket is None:
            self.socket = socket()

        self.status = ConnectionStatus.UNINITIALIZED

    def start(self):
        """Determines which starting method to call, sets socket options."""
        if self.status == ConnectionStatus.UNINITIALIZED:
            if self.server_host is not None:
                self._connect_socket(self.server_host, self.port)
            elif self.port is not None:
                self._start_listening_socket(self.port)
            self._set_socket_options()
            self.status = ConnectionStatus.CONNECTED

    def shutdown(self):
        """Puts the connection in a closed state."""
        if self.status == ConnectionStatus.CONNECTED:
            self._close_socket()
            self.status = ConnectionStatus.CLOSED

    def transmit_message(self, message):
        """Converts the Message to bytes format and sends it."""
        bytes_message = self._make_bytes(message)
        self.socket.sendall(bytes_message)
        
    def receive_message(self):
        """Attempts to receive bytes message and convert it to Message."""
        bytes_message = self._receive_message_bytes(self.socket)
        message = self._bytes_to_message(bytes_message)
        return message

    def accept_connections(self):
        """Puts the socket in listening for new connections mode."""
        return self.socket.accept()

    def _set_socket_options(self):
        """Sets the socket so the address can quickly be re-used, and it 
        times out properly when doing operations.
        """
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.settimeout(SOCKET_TIMEOUT)

    def _connect_socket(self, server_host, server_port):
        """Connects socket to the given address."""
        self.socket.connect((server_host, server_port))

    def _start_listening_socket(self, server_port):
        """Calls socket methods to put it in listening mode."""
        self.socket.bind(("", server_port))
        self.socket.listen()

    def _close_socket(self):
        """Calls socket's close method."""
        self.socket.close()

    def _receive_message_bytes(self, socket):
        """Receives the message's header, gets the length, then receives the 
        body of the message.
        """
        bytes_header = socket.recv(Message.HEADER_LENGTH)
        if len(bytes_header) == 0:
            raise ZeroLengthMessageException()
        _, _, _, _, length = self._decode_header(bytes_header)
        bytes_message_text = socket.recv(length)
        return bytes_header + bytes_message_text
    
    def _bytes_to_message(self, byte_array):
        """Converts the bytes to its component variables, then constructs a 
        Message after properly processing them.
        """
        unpacked_tuple = self._decode_header(byte_array)
        version, message_type, sender, recipient, length = unpacked_tuple
        text = byte_array[Message.HEADER_LENGTH:]
        return Message(text.decode(), sender.decode().rstrip(), recipient.decode().rstrip(), message_type, version)

    def _decode_header(self, byte_array):
        """Converts message header into a tuple of the proper types."""
        unpacked_tuple = unpack("BB" + str(SENDER_MAX_LENGTH) + "s" + str(RECIPIENT_MAX_LENGTH) + "sH", byte_array[:Message.HEADER_LENGTH])
        return unpacked_tuple

    def _make_bytes(self, message):
        """Processes the Message into bytes format for sending over socket."""
        pack_string = "BB" + str(SENDER_MAX_LENGTH) + "s" + str(RECIPIENT_MAX_LENGTH) + "sH" + str(message.length) + "s"
        data = pack(pack_string, message.version, int(message.message_type), bytes(message.sender.ljust(SENDER_MAX_LENGTH), "utf-8"), bytes(message.recipient.ljust(RECIPIENT_MAX_LENGTH), "utf-8"), message.length, bytes(message.text, "utf-8"))
        return data
