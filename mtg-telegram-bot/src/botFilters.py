import re
import botutils as bu
import config
from telegram.ext import BaseFilter

"""Filters doc : https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Advanced-Filters"""

class CardImageFilter(BaseFilter):
    """Filter use to detect if message contain a card to display"""
    def __init__(self, card_regex):
        # construct regex
        self.p = card_regex
        
    def filter(self, message):
        """"find all words between special char define in config card_char"""
        if self.p.findall(message.text): 
            return True
        else: return False
        
class DialogInfoFilter(BaseFilter):
    """Filter use to avoid card image detection when sending info to the bot in conversation handler"""
        
    def filter(self, message):
        """"find all words between special char define in config card_char"""
        if message.text.count(config.card_char) > 1: return False
        else: return True
        
class AdminsFilter(BaseFilter):
    """Grant access to bot handlers only to admins"""
        
    def filter(self, message):
        """ Return false if user is not admin in chat"""
        admins = [chatMember.user for chatMember in message.bot.get_chat_administrators(config.chat_id)]
        return message.from_user in admins
        
class ChatFilter(BaseFilter):
    """Grant access to bot handlers only to a defined chat"""
        
    def filter(self, message):
        """ Return false if user is not in authorized user list
        message doc : http://python-telegram-bot.readthedocs.io/en/stable/telegram.message.html?highlight=messag
        """
        return message.chat.id == config.chat_id