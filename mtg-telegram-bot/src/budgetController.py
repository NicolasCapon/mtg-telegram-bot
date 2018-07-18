import logging
import budgetModel as bm
import botutils as bu
import config
import botFilters
import myEnums
from myEnums import ArchivingConvStates
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

class BudgetController():
    """Class to handle dialogue around debt between members of a group"""
    
    def __init__(self, updater):
        """BudgetController constructor"""
        self.budgetModel = bm.BudgetModel()
        
        self.dispatcher = updater.dispatcher
        chat_filter = botFilters.ChatFilter()
        
        # add_transaction
        self.moneylender, self.recipient, self.amount, self.reason, self.member_validation = {}, {}, None, "", []
        self.validate_transaction_handler = CallbackQueryHandler(self.send_transaction_confirmation)
        self.transactionConvStates = myEnums.TransactionConvStates
        self.transaction_conv_entry = CommandHandler(filters=chat_filter, command='new_debt', callback=self.start_transaction_conv)
        self.dispatcher.add_handler(self.get_transaction_conversation())
        
        # archive_transactions
        self.archivingConvStates = myEnums.ArchivingConvStates
        self.arch_member_requester, self.arch_member_target, self.global_transaction = {}, {}, {}
        self.archiving_conv_entry = CommandHandler(filters=chat_filter, command='archive_debt', callback=self.start_arch_transactions)
        self.dispatcher.add_handler(self.get_archive_conversation())
        
        # send user transaction resume
        self.debt_resume_handler = CommandHandler(filters=chat_filter, command='resume_debt', callback=self.send_user_debts)
        self.dispatcher.add_handler(self.debt_resume_handler)
        
        logging.info("BudgetController OK")
        
    def get_transaction_conversation(self):
        """Create the transaction dialogue handler object"""
        dialog_info_filter = botFilters.DialogInfoFilter()
        conv_handler = ConversationHandler(
            entry_points=[self.transaction_conv_entry],

            states={
                self.transactionConvStates(1).name: [CallbackQueryHandler(self.select_transaction_amount, pattern=r'^\d{9}$')],
                self.transactionConvStates(2).name: [MessageHandler(Filters.text & dialog_info_filter, self.validate_transaction)],
                self.transactionConvStates(3).name: [CallbackQueryHandler(self.send_transaction_confirmation)]
            },

            fallbacks=[CommandHandler('stop', self.cancel)]
        )
        return conv_handler
    
    def start_transaction_conv(self, bot, update):
        """Start point of the conversation to add a transaction"""
        # Remove entry point to avoid concurrent conversations
        self.dispatcher.remove_handler(self.transaction_conv_entry)
        self.moneylender = bu.get_member_by_id(update.message.from_user.id, members=self.budgetModel.members)
        keyboard = []
        for member in self.budgetModel.update_members():
            if not member == self.moneylender:
                button = InlineKeyboardButton(member["first_name"], callback_data=str(member["id"]))
                keyboard.append([button])

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "Quel membre du groupe te doit de l'argent ?"
        update.message.reply_text(text=message,
                                  parse_mode="HTML",
                                  reply_markup=reply_markup,
                                  disable_notification=True)
        print("what")
        print(self.transactionConvStates(1).name)
        return self.transactionConvStates(1).name
        
    def select_transaction_amount(self, bot, update):
        """Get the recipient id and ask for amount"""
        query = update.callback_query
        print(query.data)
        self.recipient = bu.get_member_by_id(int(query.data), members=self.budgetModel.members)
        self.member_validation = [self.moneylender, self.recipient]
        print(self.member_validation)
        
        message = "Combien te doit <a href='tg://user?id={}'>{}</a> et pour quel motif ? (Envoie moi le montant, suivi ou non d'un motif)".format(self.recipient["id"], self.recipient["first_name"])
        print(message)
        bot.editMessageText(text=message,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            parse_mode="HTML",
                            disable_notification=True)
                            
        return self.transactionConvStates(2).name
        
    def validate_transaction(self, bot, update):
        """Show transaction resume and ask validation to moneylender"""
        try:
            # Try to match message parts with values
            reply = update.message.text.split()
            self.reason = " ".join(reply[1:])
            if not self.reason: self.reason = "NA"
            amount = reply[0].replace(",", ".").replace("€", "")
            self.amount = round(float(amount), 2)
        except ValueError:
            message = "Je n'arrive pas à extraire, le montant et/ou le motif. Reformule moi ton message stp."
            bot.sendMessage(chat_id=config.chat_id,
                            text=message,
                            disable_notification=True)
                            
            return self.transactionConvStates(2).name
        
        message = "Voici le résumé de la dette:"
        message += "\n<a href='tg://user?id={}'>{}</a> doit <b>{}€</b> à <a href='tg://user?id={}'>{}</a>, motif: <b>{}</b>.".format(self.recipient["id"], self.recipient["first_name"], self.amount, self.moneylender["id"], self.moneylender["first_name"], self.reason)
        message += "\nJ'attend une validation de la part de <b>{}</b> et <b>{}</b>.".format(self.recipient["first_name"], self.moneylender["first_name"])
        
        keyboard = [[InlineKeyboardButton("Valider", callback_data='OK'),
                     InlineKeyboardButton("Refuser", callback_data='KO')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send a message instead of replying because the recipient need to click on buttons for the validation
        bot.sendMessage(text=message,
                        chat_id=config.chat_id,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        disable_notification=False)
        
        self.dispatcher.add_handler(self.validate_transaction_handler)
        
        return self.transactionConvStates(3).name
    
    def send_transaction_confirmation(self, bot, update):
        """Send transaction confirmation which has to be confirmed by both members"""
        query = update.callback_query
        member_validation_ids = [x["id"] for x in self.member_validation]
            
        if query.data == "OK" and query.from_user.id in member_validation_ids:
            member_ok = bu.get_member_by_id(query.from_user.id, members=self.budgetModel.members)
            self.member_validation.remove(member_ok)
            if self.member_validation:
                # One member still have to validate
                message = "Voici le résumé de la dette:"
                message += "\n<a href='tg://user?id={}'>{}</a> doit <b>{}€</b> à <a href='tg://user?id={}'>{}</a>, motif: <b>{}</b>.".format(self.recipient["id"], self.recipient["first_name"], self.amount, self.moneylender["id"], self.moneylender["first_name"], self.reason)
                message += "\nJ'attend encore une validation de la part de <b>{}</b>.".format(self.member_validation[0]["first_name"])
                keyboard = [[InlineKeyboardButton("Valider", callback_data='OK'),
                             InlineKeyboardButton("Refuser", callback_data='KO')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.editMessageText(text=message,
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    parse_mode="HTML",
                                    reply_markup=reply_markup,
                                    disable_notification=True)
            
            else:
                # Transaction has been validated by both members
                self.budgetModel.add_transaction(self.moneylender, self.recipient, self.amount, self.reason)
                message = "Dette ajoutée au registre !"
                message += "\n<a href='tg://user?id={}'>{}</a> doit <b>{}€</b> à <a href='tg://user?id={}'>{}</a> (<b>{}</b>).".format(self.recipient["id"], self.recipient["first_name"], self.amount, self.moneylender["id"], self.moneylender["first_name"], self.reason)
                bot.editMessageText(text=message,
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    parse_mode="HTML",
                                    disable_notification=True)
                
                # Cleanup for next conversation
                self.reset_add_transaction_features()
                self.dispatcher.remove_handler(self.validate_transaction_handler)
                return ConversationHandler.END

        elif query.data == "KO" and query.from_user.id in member_validation_ids:
            # A member cancelled transaction
            message = "J'ai annulé la création de la dette:"
            message += "\n<a href='tg://user?id={}'>{}</a> doit <b>{}€</b> à <a href='tg://user?id={}'>{}</a> (<b>{}</b>).".format(self.recipient["id"], self.recipient["first_name"], self.amount, self.moneylender["id"], self.moneylender["first_name"], self.reason)
            message += "\n Refus de {}.".format(query.from_user.first_name)
            bot.editMessageText(text=message,
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id,
                                parse_mode="HTML",
                                disable_notification=True)
            
            # Cleanup for next conversation
            self.reset_add_transaction_features()
            self.dispatcher.remove_handler(self.validate_transaction_handler)
            return ConversationHandler.END
        
        # else: Unauthorized user press button, do nothing.
        return True

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
                self.archivingConvStates(1).name: [CallbackQueryHandler(self.verify_arch_transactions)],
                self.archivingConvStates(2).name: [CallbackQueryHandler(self.send_archiving_confirmation)]
            },

            fallbacks=[CommandHandler('stop', self.cancel)]
        )
        return conv_handler
        
    def start_arch_transactions(self, bot, update):
        """Start point of the conversation to archive all ongoing transactions between two players"""
        # Remove entry point to avoid concurrent conversations
        self.dispatcher.remove_handler(self.archiving_conv_entry)
        member_requester = bu.get_member_by_id(update.message.from_user.id, members=self.budgetModel.members)
        total_debts = self.budgetModel.get_total_debts(member_requester)
        keyboard = []
        for debt in total_debts:
            if debt["global_moneylender"]["id"] == update.message.from_user.id:
                button = InlineKeyboardButton(debt["global_recipient"]["first_name"], callback_data=str(debt["global_recipient"]["id"]))
                keyboard.append([button])
        
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = "Avec quelle personne souhaites-tu archiver les dettes courantes ?"
            update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)
            return self.archivingConvStates(1).name
        
        else:
            message = "Personne ne te doit d'argent, tu ne peux donc pas archiver de dettes."
            update.message.reply_text(message, parse_mode="HTML")
            return ConversationHandler.END
            
    def verify_arch_transactions(self, bot, update):
        """Verify debt between two members.
           Transactions can be archived only if the requester is the moneylender.
        """
        query = update.callback_query
        self.arch_member_requester = bu.get_member_by_id(query.from_user.id, members=self.budgetModel.members)
        self.arch_member_target = bu.get_member_by_id(int(query.data), members=self.budgetModel.members)
        self.global_transaction = self.budgetModel.get_debt_between_two_members(self.arch_member_requester, self.arch_member_target)
        
        message = "Es-tu certain de vouloir archiver les dettes courantes de <a href='tg://user?id={}'>{}</a> (<b>{}€</b>)?".format(self.global_transaction["global_recipient"]["id"], self.global_transaction["global_recipient"]["first_name"], self.global_transaction["global_amount"])
        keyboard = [[InlineKeyboardButton("Oui", callback_data='OK'),
                     InlineKeyboardButton("Annuler", callback_data='KO')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.editMessageText(text=message,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=reply_markup,
                            parse_mode="HTML",
                            disable_notification=True)
        
        return self.archivingConvStates(2).name
            
    def send_archiving_confirmation(self, bot, update):
        """Send resume of user actions after archiving"""
        query = update.callback_query
        if query.data == "OK":
            # Archiving
            self.budgetModel.archive_transactions(self.arch_member_requester, self.arch_member_target)
            message = "J'ai bien archivé les dettes courantes de <a href='tg://user?id={}'>{}</a> envers <a href='tg://user?id={}'>{}</a> pour un montant total de <b>{}€</b>.".format(self.global_transaction["global_recipient"]["id"], self.global_transaction["global_recipient"]["first_name"], self.global_transaction["global_moneylender"]["id"], self.global_transaction["global_moneylender"]["first_name"], self.global_transaction["global_amount"])
        
        else:
            message = "J'ai annulé ta demande d'archivage des dettes de <a href='tg://user?id={}'>{}</a> envers <a href='tg://user?id={}'>{}</a> pour un montant total de <b>{}€</b>".format(self.global_transaction["global_recipient"]["id"], self.global_transaction["global_recipient"]["first_name"], self.global_transaction["global_moneylender"]["id"], self.global_transaction["global_moneylender"]["first_name"], self.global_transaction["global_amount"])
        
        bot.editMessageText(text=message,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            parse_mode="HTML",
                            disable_notification=True)
            
        # Cleanup for next conversation
        self.reset_archiving_features()
        
        return ConversationHandler.END
    
    def send_user_debts(self, bot, update):
        """Send resume of debts implying requesting user"""
        member = bu.get_member_by_id(update.message.from_user.id, members=self.budgetModel.members)
        debts = self.budgetModel.get_total_debts(member)
        if debts:
            message = "Résumé des dettes te concernant:"
            for debt in debts:
                message += "\n<a href='tg://user?id={}'>{}</a> doit un total de {}€ à <a href='tg://user?id={}'>{}</a>.".format(debt["global_recipient"]["id"], debt["global_recipient"]["first_name"], debt["global_amount"], debt["global_moneylender"]["id"], debt["global_moneylender"]["first_name"])
        else:
            message = "Tu n'as aucune dette pour le moment petit veinard."
        
        update.message.reply_text(message, parse_mode="HTML")
        return True
        
    def reset_archiving_features(self):
        """Reset archiving variables and conversation entry handler"""
        self.arch_member_requester, self.arch_member_target, self.global_transaction = {}, {}, {}
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