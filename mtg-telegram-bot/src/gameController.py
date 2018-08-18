# coding=utf-8
import logging
import config
import gameModel as gm
import botutils as bu
from botFilters import ChatFilter, ArtGameFilter
from telegram import InputMediaPhoto, ChatAction
from telegram.ext import CommandHandler, MessageHandler, Filters


class GameController:
    """Class to handle dialogue around debt between members of a group"""

    def __init__(self, updater):
        """GameController constructor"""
        self.dispatcher = updater.dispatcher
        self.art_game = None
        self.answer_h = None
        chat_filter = ChatFilter()
        self.art_game_h = CommandHandler(filters=chat_filter, command='art_game', callback=self.start_art_game)
        self.game_scores_h = CommandHandler(filters=chat_filter, command='scores', callback=self.send_scores)
        hint_h = CommandHandler(filters=chat_filter, command='hint', callback=self.send_hint)

        self.dispatcher.add_handler(hint_h)
        self.dispatcher.add_handler(self.art_game_h)
        self.dispatcher.add_handler(self.game_scores_h)
        logging.info("GameController OK")

    def start_art_game(self, bot, update):
        """Remove entry point, start the art game and add answer handler"""
        if not self.art_game:
            message = "Chargement de la partie..."
            sent = bot.sendMessage(chat_id=config.chat_id,
                                  text=message,
                                  parse_mode="HTML",
                                  disable_notification=True,
                                  reply_to_message_id=update.message.message_id)
            bot.send_chat_action(chat_id=config.chat_id, action=ChatAction.TYPING, timeout=None)
            self.art_game = gm.GameModel(mode="art")
            user = update.message.from_user
            self.art_game.set_user(user)

            # Send photo with caption
            photo = self.art_game.card.get("image_uris", {}).get("art_crop", None)
            caption = "{} a lancé la partie !".format(self.art_game.user.first_name)
            try:
                mes = bot.send_photo(chat_id=config.chat_id, photo=photo, caption=caption)
            except:
                logging.info("ERROR while sending photo with url={}".format(photo))
                message = "Je n'arrive pas envoyer la photo de cette carte mais voici le lien : <a href='{}'>{}</a>".format(
                    photo, "carte mystère")
                mes = bot.sendMessage(chat_id=config.chat_id, text=message, parse_mode="HTML",
                                      disable_web_page_preview=True)

            bot.deleteMessage(config.chat_id, sent.message_id)
            self.art_game.set_id(mes.message_id)
            answer_filter = ArtGameFilter(self.art_game)
            self.answer_h = MessageHandler(Filters.text & answer_filter, self.answer_handler)
            self.dispatcher.add_handler(self.answer_h)

        else:
            message = "Une partie lancée par <a href='tg://user?id={}'>{}</a> est en cours...".format(
                self.art_game.user.id, self.art_game.user.first_name)
            bot.sendMessage(chat_id=config.chat_id,
                            text=message,
                            parse_mode="HTML",
                            disable_notification=True,
                            reply_to_message_id=self.art_game.id)

    def answer_handler(self, bot, update):
        """Send card photo and trophy to game winner"""
        bot.send_chat_action(chat_id=config.chat_id, action=ChatAction.TYPING, timeout=None)
        images = [{"url": self.art_game.card.get("image_uris", {}).get("normal", None),
                   "caption": self.art_game.card.get("name", "")},
                  {"url": self.art_game.trophy, "caption": "Bravo {}!".format(self.art_game.winner.first_name)}]
        album = []
        for image in images:
            album.append(InputMediaPhoto(media=image["url"], caption=image["caption"]))
        try:
            bot.send_media_group(chat_id=config.chat_id,
                                 media=album,
                                 disable_notification=False,
                                 timeout=10)
        except:
            logging.info("ERROR while sending album :")
            logging.info(media)
            for image in album:
                try:
                    bot.send_photo(chat_id=config.chat_id, photo=photo, caption=caption)
                except:
                    logging.info("ERROR while sending photo with url={}".format(image["url"]))
                    message = "Je n'arrive pas envoyer la photo de cette carte mais voici le lien : <a href='{}'>{}</a>.".format(
                        image["url"], "image link")
                    bot.sendMessage(chat_id=config.chat_id, text=message, parse_mode="HTML",
                                    disable_web_page_preview=True)

        self.dispatcher.remove_handler(self.answer_h)
        self.art_game = None

    def send_hint(self, bot, update):
        """Send hint when a game is on"""
        if self.art_game:
            bot.send_chat_action(chat_id=config.chat_id, action=ChatAction.TYPING, timeout=None)
            hint_player = update.message.from_user
            hint, hint_type = self.art_game.get_hint()
            if hint:
                message = "Voici ton indice <a href='tg://user?id={}'>{}</a>:\n{} : {}".format(hint_player.id,
                                                                                               hint_player.first_name,
                                                                                               hint_type, hint)
                bot.sendMessage(chat_id=config.chat_id,
                                text=message,
                                parse_mode="HTML",
                                disable_notification=True,
                                reply_to_message_id=self.art_game.id)
            else:
                message = "Je n'ai plus d'indice sur cette carte <a href='tg://user?id={}'>{}</a>.".format(
                    hint_player.id, hint_player.first_name)
                bot.sendMessage(chat_id=config.chat_id,
                                text=message,
                                parse_mode="HTML",
                                disable_notification=True,
                                reply_to_message_id=self.art_game.id)

    def send_scores(self, bot, update):
        """Send game ranking for each players"""
        scores = gm.get_scores()
        members = bu.load_members()
        message = ""
        for i, score in enumerate(reversed(scores)):
            if i == 0:
                message += "\U0001F947"  # First place medal
            elif i == 1:
                message += "\U0001F948"  # Second place medal
            elif i == 2:
                message += "\U0001F949"  # Third place medal
            first_name = bu.get_member_by_id(score["id"], members=members)["first_name"]
            message += "<a href='tg://user?id={}'>{}</a> - {} victoires\n".format(score["id"], first_name, score["won"])

        bot.sendMessage(chat_id=config.chat_id, text=message, parse_mode="HTML", disable_notification=True)
