import re
import logging
from time import sleep
import scryfallModel as scf
import botutils as bu
import config
from botFilters import CardImageFilter
from telegram.ext import MessageHandler, Filters

class MessageController():
    """Class to handle every text message"""
    
    def __init__(self, updater):
        """MessageController constructor"""
        self.card_regex = re.compile('\{0}(.*?)\{0}'.format(config.card_char))
        card_image_filter = CardImageFilter(self.card_regex)
        # Create handler and add it to the dispatcher
        card_detection_handler = MessageHandler(Filters.text & card_image_filter, self.simple_message_handler)
        updater.dispatcher.add_handler(card_detection_handler)
        logging.info("MessageController OK")

    def simple_message_handler(self, bot, update):
        """Use regex to find each word between special_char in a text message then send photo(s)"""
        # find all words between special_char
        cardnames = self.card_regex.findall(update.message.text)
        
        userName = update.message.from_user.first_name
        chat_id = update.message.chat_id
        cards, notFound = [], []
        for cardname in cardnames:
            card = scf.get_card_by_name(cardname)
            if card:
                cards.append(card)
            else:
                notFound.append(cardname)
        bu.send_cards_photos(cards, bot, chat_id)
        
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