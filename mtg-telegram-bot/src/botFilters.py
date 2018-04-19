import botutils as bu
from telegram.ext import BaseFilter

"""Filters doc : https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Advanced-Filters"""

class AdminFilter(BaseFilter):
    """Grant access to bot handlers only to admins"""
        
    def filter(self, message):
        """ Return false if user is not in authorized user list
        message doc : http://python-telegram-bot.readthedocs.io/en/stable/telegram.message.html?highlight=messag
        """
        admins = message.chat.get_administrators()
        return message.from_user in admins