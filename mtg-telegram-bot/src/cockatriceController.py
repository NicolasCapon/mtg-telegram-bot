import logging
import cockatriceModel as cck
import scryfallModel as scf
from telegram.ext import CommandHandler

class CockatriceController:
    """Class to manage cockatrice files and stuffs
       See https://github.com/Cockatrice/Cockatrice/wiki"""
    
    def __init__(self, updater):
        """CockatriceController constructor """
        send_xml_handler = CommandHandler('cockatrice', self.send_xml, pass_args=True)
        send_ap_handler = CommandHandler('ap', self.send_ap, pass_args=True)
        updater.dispatcher.add_handler(send_xml_handler)
        updater.dispatcher.add_handler(send_ap_handler)
        logging.info("CockatriceController OK")
        
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

    def send_ap(self, bot, update, args):
        """Send prerelease pack in .cod format for cockatrice
           Example: /ap rix"""
        arg_num = len(args)
        # Accepts only one arg for set_code
        if not arg_num == 1:
            message = "Cette fonction ne prend que 1 argument ({} donné(s))".format(arg_num)
            bot.sendMessage(chat_id=update.message.chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True)
            return False

        set_code = args[0].lower()
        cards, notes = scf.get_booster_pack(set_code, is_pr=True)
        deck_name = set_code + "_ap"
        cod_file = None
        if cards: cod_file = cck.create_deck(deck_name, sb_cards=[c.get("name", None) for c in cards], notes=notes)
        if not cod_file:
            message = "Cette édition est inconnue : [{}]".format(set_code)
            bot.sendMessage(chat_id=update.message.chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True)
            return False

        bot.sendDocument(chat_id=update.message.chat_id, document=open(cod_file, 'rb'))
        return True
