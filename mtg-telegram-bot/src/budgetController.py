import logging
import budgetModel as bu
from myEnums import TransactionConvStates
from telegram.ext import ConversationHandler

class BudgetController():
    """Class to handle dialogue around debt between members of a group"""
    
    def __init__(self, updater):
        """BudgetController constructor"""
        self.budgetModel = bu.BudgetModel()
        self.moneylender, self.recipient, self.amount, self.reason = {}, {}, None, ""
        
        self.dispatcher = updater.dispatcher
        self.transaction_conv_entry = CommandHandler('new_debt', self.start_transaction_conv)
        self.dispatcher.add_handler(get_transaction_conversation)
        
        
    def get_transaction_conversation(self, bot, update):
        """Create the transaction dialogue handler object"""
        conv_handler = ConversationHandler(
            entry_points=[self.transaction_conv_entry],

            states={
                TransactionConvStates.SELECT_AMOUNT: [CallbackQueryHandler(self.select_transaction_amount)],
                TransactionConvStates.CONFIRM_TRANSACTION: [MessageHandler(Filters.text, self.validate_transaction)],
                TransactionConvStates.VALIDATE: [CallbackQueryHandler(self.send_transaction_confirmation)]
            },

            fallbacks=[CommandHandler('stop', self.cancel)]
        )
        return conv_handler
    
    def start_transaction_conv(self, bot, update):
        """Start point of the conversation to add a transaction"""
        # Remove entry point to avoid concurrent conversations
        self.dispatcher.remove_handler(self.transaction_conv_entry)
        self.moneylender = update.message.from_user.first_name
        # self.box_userName = update.message.from_user.first_name
        keyboard = []
        for member in self.budgetModel.members:
            button = InlineKeyboardButton(member["first_name"], callback_data=member["id"])
            keyboard.append(button)

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "Quel membre du groupe te doit de l'argent ?"
        update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)
        
        return TransactionConvStates.SELECT_AMOUNT
        
    def select_transaction_amount(self, bot, update):
        """Get the recipient id and ask for amount"""
        query = update.callback_query
        for member in self.budgetModel.members:
            if str(member["id"]) == query.data:
                self.recipient = member
                break
        
        message = "Combien te doit <b>{}</b> et pour quel motif ? (Envoie moi le montant, suivi ou non d'un motif)".format(self.recipient["first_name"])
        bot.editMessageText(text=message,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            parse_mode="HTML")
        
        return TransactionConvStates.CONFIRM_TRANSACTION
        
    def validate_transaction(self, bot, update):
        """Show transaction resume and ask validation to moneylender"""
        try:
            # Try to match message parts with values
            reply = update.message.text.split()[0]
            self.reason = reply[1:]
            amount = reply[0].replace(",", ".").replace("€", "")
            self.amount = round(int(amount), 2)
        except ValueError:
            message = "Je n'arrive pas à extraire, le montant et/ou le motif. Reformule moi ton message stp."
            bot.sendMessage(update.message.chat_id, message)
            return TransactionConvStates.CONFIRM_TRANSACTION
        
        if self.reason:
            message = "Voici le résumé de la dette :\n<b>{}</b> te doit <b>{}€</b>, motif : <b>{}</b>.".format(self.recipient["first_name"], self.amount, self.reason)
        else:
            message = "Voici le résumé de la dette :\n<b>{}</b> te doit <b>{}€</b> (aucun motif).".format(self.recipient["first_name"], self.amount, self.reason)
            
        keyboard = [[InlineKeyboardButton("Valider", callback_data='OK'),
                    InlineKeyboardButton("Annuler", callback_data='KO')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)
        
        return TransactionConvStates.VALIDATE
    
    def send_transaction_confirmation()
        """Save transaction and send resume"""
        bu.add_transaction(self.moneylender, self.recipient, self.amount, self.reason)
        
        if self.reason:
            message = "Dette ajoutée au registre !\n<b>{}</b> doit <b>{}€</b> à <b>{}</b>, motif : <b>{}</b>".format(self.recipient, self.amount, self.moneylender, self.reason)
        else:
            message = "Dette ajoutée au registre !\n<b>{}</b> doit <b>{}€</b> à <b>{}</b>, motif : <b>{}</b>".format(self.recipient, self.amount, self.moneylender)
        
        bot.editMessageText(text=message,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            parse_mode="HTML")
                            
        # Reset values
        self.moneylender, self.recipient, self.amount, self.reason = {}, {}, None, ""
        # Enable conversation handlers
        self.dispatcher.add_handler(self.transaction_conv_entry)
        
        return ConversationHandler.END
        
    def cancel(self, bot, update):
        """Cancel ongoing conversation, reset states and handlers"""
        logger = logging.getLogger(__name__)
        logger.info("User %s canceled the conversation." % update.message.from_user.first_name)
        # Reset values
        self.moneylender, self.recipient, self.amount, self.reason = {}, {}, None, ""
        # Enable conversation handlers
        self.dispatcher.add_handler(self.transaction_conv_entry)
        
        return ConversationHandler.END
    