import re
import logging
import urllib.request
from time import sleep
import scryfallAPI as scf
from telegram.ext import MessageHandler, Filters

class MessageManager():
    """Class to handle every text message"""
    
    def __init__(self, updater):
        """MessageManager constructor"""
        # Create handler and add it to the dispatcher
        msg_h = MessageHandler(Filters.text, self.simple_message_handler)
        updater.dispatcher.add_handler(msg_h)
        logging.info("MessageManager OK")

    def simple_message_handler(self, bot, update):
        """Use regex to detect specific pattern in text message then apply specific function"""
        answer = update.message.text
        self.image_filter(answer, bot, update)
        return True 
        
    def image_filter(self, text, bot, update):
        """Use regex to find each word between special_char in a text message then send photo(s)"""
        special_char = "*"
        # construct regex
        p = re.compile('\{0}(.*?)\{0}'.format(special_char))
        # find all words between special_char
        cardnames = p.findall(text)
        
        userName = update.message.from_user.first_name
        chat_id = update.message.chat_id
        cards, notFound = [], []
        for cardname in cardnames:
            card = scf.get_card_by_name(cardname)
            if card:
                cards.append(card)
            else:
                notFound.append(cardname)
        scf.send_cards_photos(cards, bot, chat_id)
        
        # If cards were not found, send a informative message
        if notFound :
            message = "Désolé {}, je ne trouve pas l'illustration de la ou les carte(s) suivante(s):\n".format(userName)
            for cardname in notFound: 
                message += "- " + cardname + "\n"
            sent = bot.sendMessage(chat_id, message)
            sleep(10)
            bot.deleteMessage(chat_id, sent.message_id)
            return False
        return True