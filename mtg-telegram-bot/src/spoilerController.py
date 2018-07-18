import re
import os
import time
import json
import praw
import logging
import scryfallModel as scf
import botutils as bu
import datetime
import config
from collections import OrderedDict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, Filters
from telegram.error import (TelegramError, TimedOut, NetworkError)

class SpoilerController:
    """Class to detect and handle spoilers from different sources across the web:
       - https://www.reddit.com/r/magicTCG/
       - https://scryfall.com/"""
    
    def __init__(self, updater):
        """Initialize SpoilerController tasks
           use a lot the job_queue mechanics 
           https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-JobQueue"""
        
        self.chat_ID = config.chat_id
        
        self.spoiler_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "spoilers.json")
        self.last_spoilers_review = ""
              
        self.reddit = self.log_to_reddit()
        self.last_reddit_review = time.time()
        self.duplicate = {"sub_ids":[], "sub_titles":[]}
        
        # Add functionalities
        # updater.job_queue.run_repeating(self.spoilers_review_auto, interval=config.spoiler_review_timer, first=0)
        updater.job_queue.run_repeating(self.reddit_crawler, interval=config.reddit_crawler_timer, first=0)
        updater.job_queue.run_repeating(self.reset_duplicates, interval=86400*7, first=86400*7) # Reset spoilers duplicate memory every week
        spoilers_review_handler = CommandHandler("spoilers_review", self.spoilers_review_manual)
        updater.dispatcher.add_handler(spoilers_review_handler)
        
        self.ranks = OrderedDict([('0', "\U0001F929"), ('1', "\U0001F600"), ('2', "\U0001F610"), ('3', "\U0001F922")])
        updater.dispatcher.add_handler(CallbackQueryHandler(self.rank_spoiler_callback, pattern=r'^\{(.*?)\}$'))
        
        logging.info("SpoilerController OK")
    
    def log_to_reddit(self):
        """Log to reddit API and return a subreddit object"""
        
        reddit = praw.Reddit(client_id=config.reddit_client_id,
                             client_secret=config.reddit_client_secret,
                             password=config.reddit_password,
                             user_agent=config.reddit_user_agent,
                             username=config.reddit_username)
        
        return reddit
                                    
    def reddit_crawler(self, bot, job):
        """Crawl submissions of a subreddit to find a spoiler between now and the last run
           Use this function with a job_queue run_repeating"""
        end_time = time.time()
        # Testing :
        # for submission in [self.reddit.submission(id = "8rl2e0")]:
            # if True:
        for submission in self.reddit.subreddit("magicTCG").new():
            if submission.created_utc > self.last_reddit_review and self.is_reddit_spoiler(submission) and not self.is_reddit_duplicate(submission):                
                # Store submission id and transformed title for future duplicate detections
                self.duplicate["sub_ids"].append(submission.id)
                self.duplicate["sub_titles"].append(self.title_for_comp(submission.title))
                
                # Prepare message for chat
                link = "https://www.reddit.com" + submission.permalink
                message = "Je crois que j'ai trouvé un spoiler ! \U0001F916\U0001F50E\n<a href='{}'>{}</a>\nAvis:".format(link, submission.title)
                keyboard = [[]]
                for key, value in self.ranks.items():
                    button = InlineKeyboardButton(value, callback_data=json.dumps({"rank":key,"users":[]}))
                    keyboard[0].append(button)
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                bot.sendMessage(chat_id=self.chat_ID,
                                text=message,
                                parse_mode="HTML",
                                reply_markup=reply_markup,
                                disable_web_page_preview=True)
                # If submission has preview image, send photo with caption of reddit link
                if hasattr(submission, 'preview') :
                    image_url = submission.preview.get("images", [])[0].get("source").get("url")
                    bot.sendPhoto(chat_id=self.chat_ID,
                                  photo=image_url,
                                  disable_notification=True)       
        
        # Reset the last review timestamp
        self.last_reddit_review = end_time
        return True
    
    def rank_spoiler_callback(self, bot, update):
        query = update.callback_query
        callback_data = json.loads(query.data)
        user_id = query.from_user.id
        
        if query.message.entities and not user_id in callback_data["users"]:
            callback_data["users"].append(user_id)
            url = query.message.entities[0].url
            initial_text = query.message.text.split("\n")
            initial_text[1] = "<a href='{}'>{}</a>".format(url, initial_text[1])
            
            message = "\n".join(initial_text) + " " + self.ranks[callback_data["rank"]]
            keyboard = [[]]
            for key, value in self.ranks.items():
                button = InlineKeyboardButton(value, callback_data=json.dumps({"rank":key,"users":callback_data["users"]}))
                keyboard[0].append(button)
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(text=message,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  parse_mode="HTML",
                                  reply_markup=reply_markup,
                                  disable_web_page_preview=True,
                                  disable_notification=True)
        
        return True
                          
    def is_reddit_spoiler(self, submission):
        """Determine if a submission is a spoiler. For regex see : http://rubular.com/r/bgixv2J6yF"""
        
        # Discard any submission containing no external link to a potential spoiler
        p = re.compile(".*\[(\w{3})\].*")
        m = p.match(submission.title)
        if submission.domain == "self.magicTCG":
            return False
        elif submission.spoiler == "True":
            logging.info("Reddit spoiler detected : [{}] {}".format(submission.id, submission.title))
            return True
        elif m:
            code = m.group(1).lower()
            set_list = scf.get_set_list()
            futur_sets, old_sets = [], []
            is_old = False
            now = datetime.datetime.now()
            # sets in set_list are ordered from newest to oldest
            for edition in set_list:
                set_code = edition.get("code", "")
                if len(set_code) != 3: 
                    continue
                elif not is_old and now > datetime.datetime.strptime(edition.get("released_at", "3000-01-01"),'%Y-%m-%d'):
                    # If we encounter an old set, all remaining sets are also old
                    is_old = True
                
                if not is_old:
                    futur_sets.append(set_code)
                else:
                    old_sets.append(set_code)
            
            # recurring codes that don't correspond to a Magic set
            unwanted_codes = ["rpl","edh","tcc","psa","cfb","diy","d&d",
                              "b&r","rob","wmc","gds","abc","art","lsv",
                              "til","fun","lrr", "wip"]
            
            # submission title contain 3 letters in between brackets that doesn't match an old set code

            if code in futur_sets:
                logging.info("Reddit spoiler detected : [{}] {}".format(submission.id, submission.title))
                return True
            elif code in old_sets or code in unwanted_codes:
                return False
            else:
                logging.info("Reddit spoiler detected : [{}] {}".format(submission.id, submission.title))
                return True
        else:
            return False
    
    def is_reddit_duplicate(self, submission):
        """Try to avoid duplicates between reddit posts"""
        
        # Test if submission code is knowned
        if submission.id in self.duplicate["sub_ids"]:
            logging.info("Reddit spoiler duplicate detected on id: [{}] {}".format(submission.id, submission.title))
            return True
        
        # Test if submission title is a fuzzy duplicate of a recent one and compare if one title is in another title
        # Example: "[DOM] Test" and "[DOM] Test - TCC revealed card"
        title_comp = self.title_for_comp(submission.title)
        for sub_title in self.duplicate["sub_titles"]:
            if title_comp in sub_title or sub_title in title_comp:
                logging.info("Reddit spoiler duplicate detected on title: [{}] {}".format(submission.id, submission.title))
                return True
        
        return False

    def title_for_comp(self, s):
        """Function used to prepare string from submission title for duplicate detection
           Find and Remove the three letters set [EXT] from string
           Then remove all special character and upper-case letters from string"""
        
        p = re.compile(".*\[(\w{3})\].*")
        m = p.match(s)
        s = s.replace(m.group(1), "").lower()
        # Remove special characters and spaces
        s = ''.join(e for e in s if e.isalnum())
        
        return s
        
    def reset_duplicates(self, bot, job): 
        """Reset duplicate memory
           Use this function with a job_queue run_repeating"""
           
        self.duplicate = {"sub_ids":[], "sub_titles":[]}
        
        return True
        
    def spoilers_review_auto(self, bot, job):
        """Job_queue needs function with bot and job as parameter only"""
        
        self.spoilers_review(bot)
        return True
    
    def spoilers_review_manual(self, bot, update):
        """dispatcher needs function with bot and update as parameter only"""
        
        self.spoilers_review(bot, mode="manual")
        return True
        
    def spoilers_review(self, bot, mode="auto"):
        """Send photo of all new spoilers published since the last run"""
        
        logging.info("Start the spoiler_review...")
        spoilers, dump_data = self.get_new_spoilers()
        if not spoilers and mode == "manual":
            message = "Aucun spoiler detecté depuis le {}.".format(self.last_spoilers_review)
            bot.sendMessage(chat_id=self.chat_ID,
                            text=message,
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            self.last_spoilers_review = datetime.datetime.now()                            
        elif not spoilers and mode == "auto": 
            self.last_spoilers_review = datetime.datetime.now()
            return False
        logging.info("{} new spoilers detected.".format(len(spoilers)))
        # Get each sets from spoilers
        sets_code = set([spoiler.get("set", None) for spoiler in spoilers])
        for set_code in sets_code:
            edition = scf.get_set(set_code)
            release_date = edition.get("released_at", None)
            if release_date:
                release = datetime.datetime.strptime(release_date,'%Y-%m-%d')
                dif = release - datetime.datetime.now()
                countdown = dif.days
                # spiral calendar emoji: \U0001F5D3
                message = 'Résumé des spoilers <a href="{}">{}</a> [\U0001F5D3J-{}]'.format(edition.get("scryfall_uri", ""), edition.get("name", ""), countdown)
            else: 
                message = 'Résumé des spoilers <a href="{}">{}</a> !'.format(edition.get("scryfall_uri", ""), edition.get("name", ""))
            try:
                bot.sendMessage(chat_id=self.chat_ID,
                                text=message,
                                parse_mode="HTML",
                                disable_web_page_preview=True)
            except (TimedOut, TelegramError, NetworkError) as e:
                logging.error('A TimeOut or TelegramError exception occurred: {}'.format(e))
            except:
                e = sys.exc_info()[0]
                logging.error('An exception occurred: {}'.format(e))
            # Loop in spoilers of specific set
            cardlist = [spoiler for spoiler in spoilers if spoiler.get("set", None) == set_code]
            bu.send_cards_photos(cardlist, bot, self.chat_ID, disable_notification=True)
        
        # Add new spoilers to the spoiler track file
        with open(self.spoiler_file, 'w') as file:
            json.dump(dump_data, file)
        self.last_spoilers_review = datetime.datetime.now()
        return True
    
    def get_new_spoilers(self):
        """Return a list of scryfall card object for each new card detected"""
        
        # Load previous spoilers from json file
        with open(self.spoiler_file, 'r') as file:
            content = json.load(file)
        old_spoilers = set(content)
        spoilers, dump_data = [], []
        futur_sets = scf.get_futur_sets()
        # Create list of all futur cards
        for edition in futur_sets:
            for card in scf.get_cards_list(edition):
                spoilers.append(card)
                # We only store card id in json file
                dump_data.append(card["id"])
        # Return only card that wasn't in json file
        return [card for card in spoilers if card["id"] not in old_spoilers], dump_data