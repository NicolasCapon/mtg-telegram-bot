# Import dependencies
import config
import spoilerManager, messageManager, cockatriceManager
import logging
from telegram.ext import Updater

def main():
    """Initiate bot instance with all the functionalities"""
    
    # Set up basic logging
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log", "console.log")
    logging.basicConfig(format='%(asctime)s %(message)s', filename=log_file, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token=config.telegram_token)
    
    # Add features
    messageManager.MessageManager(updater)
    cockatriceManager.CockatriceManager(updater)
    spoilerManager.SpoilerManager(updater)
    
    # log all errors
    updater.dispatcher.add_error_handler(error)
    
    # Start the Bot
    updater.start_polling()
    logger.info("GeekstreamBot started")
    
    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    
def error(bot, update, error):
    """Generic handler for errors"""
    
    logger = logging.getLogger(__name__)
    logger.warn('Update "%s" caused error "%s"' % (update, error))

if __name__ == '__main__':
    main()