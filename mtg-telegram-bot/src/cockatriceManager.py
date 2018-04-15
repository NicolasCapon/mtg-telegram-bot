import sys
import logging
sys.path.append("/home/pi/telegram/shared/sources")
import myEnums
import cockatriceAPI as cck
import scryfallAPI as scf
from telegram.ext import CommandHandler

class CockatriceManager:
    """Class to manage cockatrice files and stuffs
       See https://github.com/Cockatrice/Cockatrice/wiki"""
    
    def __init__(self, updater):
        """CockatriceManager constructor """
        send_xml_handler = CommandHandler('cockatrice', self.send_xml, pass_args=True)
        updater.dispatcher.add_handler(send_xml_handler)
        logging.info("CockatriceManager OK")
        
    def send_xml(self, bot, update, args):
        """Send xml custom set file to chat
           Example: /cockatrice rix"""
        arg_num = len(args)
        # Accepts only one arg for set_code
        if not arg_num == 1:
            message = "Cette fonction ne prend que 1 argument ({} donné(s))".format(arg_num)
            bot.sendMessage(chat_id=update.message.chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True)
            return False
            
        set_code = args[0]
        xml_file = cck.get_cockatrice_file(set_code)
        if not xml_file:
            message = "Cette édition est inconnue : [{}]".format(set_code)
            bot.sendMessage(chat_id=update.message.chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True)
            return False

        bot.sendDocument(chat_id=update.message.chat_id, document=open(xml_file, 'rb')) 
        return True