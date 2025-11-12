from logs.logger import logger


class BaseMemory():

    def __init__(self):
        self.messages = []

    def add_message(self, message):
        """添加一条消息到记忆中"""
        self.messages.append(message)

    def get_all_messages(self):
        """获得记忆中所有消息内容"""
        return self.messages

    def get_last_message(self):
        """获得记忆中最后一条消息内容"""
        return self.messages[-1]['content']
