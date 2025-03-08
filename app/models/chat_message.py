from enum import Enum

class MessengerType(str, Enum):
    user = 'user'
    bot = 'bot'


class ChatMessage:
    def __init__(self):
        pass