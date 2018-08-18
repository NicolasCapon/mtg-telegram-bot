import botutils
import logging
from botFilters import AdminsFilter
from telegram.ext import MessageHandler, CommandHandler, Filters


class AdminController:
    """Class to add admin features"""
    
    def __init__(self, updater):
        """MessageController constructor"""
        self.dispatcher = updater.dispatcher
        
        admin_filter = AdminsFilter()
        
        # Add user detection feature
        self.user_handler = MessageHandler(filters=Filters.all, callback=self.detect_users_handler)
        self.members = []
        
        # Enable detection
        self.user_detection_enabler = CommandHandler(filters=admin_filter, command='detect_users', callback=self.enable_user_detection, pass_args=True)
        
        updater.dispatcher.add_handler(self.user_detection_enabler)
        
        logging.info("AdminController OK")
        
    def enable_user_detection(self, bot, update, args):
        """Start or stop detect_users_handler, pass arg 0 or 1 to activate"""
        mode = args[0]
        if mode == "1":
            self.members = botutils.load_members()
            self.dispatcher.add_handler(self.user_handler)
            message = "User detection enabled"
        else:
            self.dispatcher.remove_handler(self.user_handler)
            message = "User detection disabled"
        
        update.message.reply_text(message, parse_mode="HTML")
        return True
        
    def detect_users_handler(self, bot, update):
        """Parse every message to detect new user"""
        user = update.message.from_user
        if not user in self.members:
            botutils.register_user(user=user, ref_members=self.members)