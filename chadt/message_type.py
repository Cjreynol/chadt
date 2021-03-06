from enum import Enum


class MessageType(Enum):
    """Represents the different messages sent between server and clients.

    Each grouping is a class of related messages that are used to provide 
    certain functionality to the clients or server.

    """

    TEXT = 1

    DISCONNECT = 11

    USERNAME_REQUEST = 20
    USERNAME_ACCEPTED = 21
    USERNAME_REJECTED = 22
    TEMP_USERNAME_ASSIGNED = 23

    LIST_OF_USERS = 30
    USER_CONNECT = 31
    USER_NAME_CHANGE = 32
    USER_DISCONNECT = 33
    
    ERROR = 90

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name
