import logging
import budgetModel as bm
import botutils as bu
from myEnums import TransactionConvStates
from telegram.ext import ConversationHandler

class BudgetController():
    """Class to handle dialogue around debt between members of a group"""
    
    def __init__(self, updater):
        """BudgetController constructor"""
        self.budgetModel = bu.BudgetModel()
        
        self.dispatcher = updater.dispatcher
        
        # add_transaction variables
        self.moneylender, self.recipient, self.amount, self.reason, self.member_validation = {}, {}, None, "", []
        self.transaction_conv_entry = CommandHandler('new_debt', self.start_transaction_conv)
        self.dispatcher.add_handler(self.get_transaction_conversation)
        
        # archive_transactions variables
        self.global_transaction = {}
        self.archiving_conv_entry = CommandHandler('new_debt', self.start_arch_transactions)
        self.dispatcher.add_handler(self.get_archive_conversation)
        
    def get_transaction_conversation(self):
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
        self.moneylender = update.message.from_user
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
        self.recipient = bu.get_member_by_id(int(query.data))
        self.member_validation = [self.moneylender, self.recipient]
        
        message = "Combien te doit <b>{}</b> et pour quel motif ? (Envoie moi le montant, suivi ou non d'un motif)".format(self.recipient["first_name"])
        bot.editMessageText(text=message,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            parse_mode="HTML",
                            disable_notification=True)
        
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
            message = "Voici le résumé de la dette :"
            message += "\n<pre><b>{}</b> te doit <b>{}€</b>, motif : <b>{}</b>.</pre>".format(self.recipient["first_name"], self.amount, self.reason)
            message += "\nJ'attend une validation de la part de <b>{}</b> et <b>{}</b>."
        else:
            message = "Voici le résumé de la dette :"
            message += "\n<pre><b>{}</b> te doit <b>{}€</b> (aucun motif).</pre>".format(self.recipient["first_name"], self.amount, self.reason)
            message += "\nJ'attend une validation de la part de <b>{}</b> et <b>{}</b>."
            
        keyboard = [[InlineKeyboardButton("Valider", callback_data='OK'),
                     InlineKeyboardButton("Refuser", callback_data='KO')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send a message instead of replying because the recipient need to click on buttons for the validation
        bot.sendMessage(text=message,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        disable_notification=False)
        
        return TransactionConvStates.VALIDATE
    
    def send_transaction_confirmation(self, bot, update):
        """Send transaction confirmation which has to be confirmed by both members"""
        query = update.callback_query
        
        if not query.from_user.id in self.member_validation:
            # Unauthorized user press button, do nothing.
            return TransactionConvStates.VALIDATE
            
        elif query.data == "OK" and query.from_user.id in self.member_validation:
            self.member_validation.remove(query.from_user.id)
            if self.member_validation:
                # One member still have to validate
                message = "Voici le résumé de la dette :"
                message += "\n<pre><b>{}</b> te doit <b>{}€</b> (aucun motif).</pre>".format(self.recipient["first_name"], self.amount, self.reason)
                message += "\nJ'attend une validation de la part de <b>{}</b>.".format(self.member_validation[0])
                keyboard = [[InlineKeyboardButton("Oui", callback_data='OK'),
                             InlineKeyboardButton("Annuler", callback_data='KO')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.editMessageText(text=message,
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    parse_mode="HTML",
                                    reply_markup=reply_markup,
                                    disable_notification=True)
                
                return TransactionConvStates.VALIDATE
            
            else:
                # Transaction has been validated by both members
                bu.add_transaction(self.moneylender, self.recipient, self.amount, self.reason)
                message = "Dette ajoutée au registre !"
                message += "\n<b>{}</b> doit <b>{}€</b> à <b>{}</b> (<b>{}</b>).".format(self.recipient, self.amount, self.moneylender, self.reason)
                bot.editMessageText(text=message,
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    parse_mode="HTML",
                                    disable_notification=True)
                
                # Cleanup for next conversation
                self.reset_add_transaction_features()
        
                return ConversationHandler.END

        else:
            # A member cancelled transaction
            message = "J'ai annulé la création de la dette :"
            message += "\n<b>{}</b> doit <b>{}€</b> à <b>{}</b> (<b>{}</b>).".format(self.recipient, self.amount, self.moneylender, self.reason)
            message += "\n Refus de {}.".format(query.from_user.id)
            bot.editMessageText(text=message,
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id,
                                parse_mode="HTML",
                                disable_notification=True)
            
            # Cleanup for next conversation
            self.reset_add_transaction_features()
            
            return ConversationHandler.END

    def reset_add_transaction_features(self):
        """Reset archiving variables and conversation entry handler"""
        self.moneylender, self.recipient, self.amount, self.reason, self.member_validation = {}, {}, None, "", []
        self.dispatcher.add_handler(self.transaction_conv_entry)
        return True
            
    def get_archive_conversation(self):
        """Create the transaction dialogue handler object"""
        conv_handler = ConversationHandler(
            entry_points=[self.archiving_conv_entry],

            states={
                TransactionConvStates.VERIFY_ARCHIVING: [CallbackQueryHandler(self.verify_arch_transactions)],
                TransactionConvStates.CONFIRM_ARCHIVING: [CallbackQueryHandler(self.send_archiving_confirmation)]
            },

            fallbacks=[CommandHandler('stop', self.cancel)]
        )
        return conv_handler
        
    def start_arch_transactions(self, bot, update):
        """Start point of the conversation to archive all ongoing transactions between two players"""
        # Remove entry point to avoid concurrent conversations
        self.dispatcher.remove_handler(self.archiving_conv_entry)
        # self.box_userName = update.message.from_user.first_name
        keyboard = []
        for member in self.budgetModel.members:
            button = InlineKeyboardButton(member["first_name"], callback_data=member["id"])
            keyboard.append(button)

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "Avec quelle personne souhaites-tu archiver les dettes courantes ?"
        update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)
        
        return TransactionConvStates.VERIFY_ARCHIVING
        
    def verify_arch_transactions(self, bot, update):
        """Verify debt between two members.
           Transactions can be archived only if the requester is the moneylender.
        """
        query = update.callback_query
        self.global_transaction = bu.get_debt_between_two_members(query.from_user.id, int(query.data))
        if query.from_user.id == self.global_transaction["global_recipient"]:
            # Requester is the recipient and cannot archive ongoing transactions
            message = "Seul la personne ayant prêté de l'argent peut archiver des dettes. Demande à <b>{}</b> de faire ça pour toi.".format(self.global_transaction["global_moneylender"])
            bot.editMessageText(text=message,
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id,
                                parse_mode="HTML")
            
            # Cleanup for next conversation
            self.reset_archiving_features()
            
            return ConversationHandler.END
        
        else:
            # Requester is the moneylender and can archive ongoing transactions
            message = "Es-tu certain de vouloir archiver les dettes courantes de <b>{}</b> (<b>{}€</b>)?".format(self.global_transaction["global_recipient"], self.global_transaction["global_amount"])
            keyboard = [[InlineKeyboardButton("Oui", callback_data='OK'),
            InlineKeyboardButton("Annuler", callback_data='KO')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.editMessageText(text=message,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=reply_markup,
                            parse_mode="HTML")
            
            return TransactionConvStates.CONFIRM_ARCHIVING
            
    def send_archiving_confirmation(self, bot, update):
        query = update.callback_query
        if query.date == "OK":
            message = "J'ai bien archivé les dettes courantes de <b>{}</b> envers <b>{}</b> pour un montant total de <b>{}</b>.".format(self.global_transaction["global_recipient"],self.global_transaction["global_moneylender"], self.global_transaction["global_amount"])
            bot.editMessageText(text=message,
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                parse_mode="HTML")
            
            # Cleanup for next conversation
            self.reset_archiving_features()
            
            return ConversationHandler.END
        
        else:
            message = "J'ai annulé ta demande d'archivage des dettes de <b>{}</b> envers <b>{}</b> pour un montant total de <b>{}</b>".format(self.global_transaction["global_recipient"],self.global_transaction["global_moneylender"], self.global_transaction["global_amount"])
            bot.editMessageText(text=message,
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                parse_mode="HTML")
            
            # Cleanup for next conversation
            self.reset_archiving_features()
            
            return ConversationHandler.END

    def reset_archiving_features(self):
        """Reset archiving variables and conversation entry handler"""
        self.global_transaction = {}
        self.dispatcher.add_handler(self.archiving_conv_entry)
        return True
        
    def cancel(self, bot, update):
        """Cancel ongoing conversation, reset states and handlers"""
        logger = logging.getLogger(__name__)
        logger.info("User %s cancelled the conversation." % update.message.from_user.first_name)
        # Reset all conversations
        self.reset_archiving_features()
        self.reset_add_transaction_features()

        return ConversationHandler.END