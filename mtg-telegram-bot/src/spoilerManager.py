import praw
import re
import sys
import time
import json
import logging
import scryfallAPI as scf
import func_utils as fu
import datetime
import config
from telegram import InputMediaPhoto
from telegram.ext import CommandHandler

class SpoilerManager:
    """Class to detect and handle spoilers from different sources across the web:
       - https://www.reddit.com/r/magicTCG/
       - https://scryfall.com/"""
    
    def __init__(self, updater):
        """Initialize SpoilerManager tasks
           use a lot the job_queue mechanics 
           https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-JobQueue"""
        
        # self.chat_ID = 257145716 # Private chat
        self.chat_ID = config.chat_id # GeekStream chat
        
        self.spoiler_file = '/home/pi/telegram/GeekStreamBot/spoilers/spoilers.json'
        self.last_spoilers_review = ""
              
        self.reddit = self.log_to_reddit()
        self.last_reddit_review = time.time()
        self.duplicate = {"sub_ids":[], "sub_titles":[]}
        
        # Add functionalities
        # Too many TimeOut Exceptions : updater.job_queue.run_once(self.start_reddit_stream, 0)
        updater.job_queue.run_repeating(self.spoilers_review_auto, interval=3600*12, first=0)
        updater.job_queue.run_repeating(self.reddit_crawler, interval=60*2, first=0)
        updater.job_queue.run_repeating(self.reset_duplicates, interval=86400*7, first=0) # Reset spoilers duplicate memory every week
        spoilers_review_handler = CommandHandler("spoilers_review", self.spoilers_review_manual)
        updater.dispatcher.add_handler(spoilers_review_handler)
        
        logging.info("SpoilerManager OK")
    
    def log_to_reddit(self):
        """Log to reddit API and return a subreddit object"""
        
        reddit = praw.Reddit(client_id=config.reddit_client_id,
                             client_secret=config.reddit_client_secret,
                             password=config.reddit_password,
                             user_agent=config.reddit_user_agent,
                             username=config.reddit_username)
        
        return reddit
    
    def start_reddit_stream(self, bot, job):
        """Connect to reddit and start streaming all submission of magicTCG subreddit to detect spoilers
           WARNING : Cause TimeOut exceptions after a random period of time"""

        reddit = praw.Reddit(client_id=config.reddit_client_id,
                             client_secret=config.reddit_client_secret,
                             password=config.reddit_password,
                             user_agent=config.reddit_user_agent,
                             username=config.reddit_username)
            
        subreddit = reddit.subreddit('magicTCG')
        logging.info("start streaming reddit...")
        start_time = time.time()
        # sub_ids = ["80d9ew"]#["7nlmye", "7nltgq", "7nv757", "7o32qx"]#, "7nln6c", "7hsqy5", "7eflae", "79n4vv", "7e93ed", "79o4r9", "7kodqn", "7n2c2n", "7cnuja"]
        # for sub_id in sub_ids:
            # submission = reddit.submission(id = sub_id)
            # print(self.is_reddit_spoiler(submission))
        for submission in subreddit.stream.submissions():
            if submission.created_utc > start_time : 
                logging.info("Reddit submission detected : {}".format(submission.id))
            if submission.created_utc > start_time and self.is_reddit_spoiler(submission):
                logging.info("Reddit spoiler detected : {}".format(submission.id))
                link = "https://www.reddit.com" + submission.permalink
                # robot : \U0001F916 magnifying glass : \U0001F50E See : https://unicode.org/emoji/charts/full-emoji-list.html
                message = "Je crois que j'ai trouvé un spoiler ! \U0001F916\U0001F50E\n<a href='{}'>{}</a>".format(link, submission.title)
                # If submission has preview image, send photo with caption of reddit link
                if hasattr(submission, 'preview') :
                    bot.sendMessage(chat_id=self.chat_ID,
                                    text=message,
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)
                    image_url = submission.preview.get("images", [])[0].get("source").get("url")
                    bot.sendPhoto(chat_id=self.chat_ID,
                                  photo=image_url,
                                  disable_notification=True)
                                  
                # Otherwise, send only the submission link
                else:
                    bot.sendMessage(chat_id=self.chat_ID,
                                    text=message,
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)
                                    
    def reddit_crawler(self, bot, job):
        """Crawl submissions of a subreddit to find a spoiler between now and the last run
           Use this function with a job_queue run_repeating"""
        
        end_time = time.time()
        for submission in self.reddit.subreddit("magicTCG").new():
            if submission.created_utc > self.last_reddit_review and self.is_reddit_spoiler(submission) and not is_reddit_duplicate(submission):                
                # Store submission id and transformed title for future duplicate detections
                self.duplicate["sub_ids"].append(submission.id)
                self.duplicate["sub_titles"].append(self.title_for_comp(submission.title))
                
                # Prepare message for chat
                link = "https://www.reddit.com" + submission.permalink
                message = "Je crois que j'ai trouvé un spoiler ! \U0001F916\U0001F50E\n\<a href='{}'>{}</a>".format(link, submission.title)
                
                # If submission has preview image, send photo with caption of reddit link
                if hasattr(submission, 'preview') :
                    bot.sendMessage(chat_id=self.chat_ID,
                                    text=message,
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)
                    image_url = submission.preview.get("images", [])[0].get("source").get("url")
                    bot.sendPhoto(chat_id=self.chat_ID,
                                  photo=image_url,
                                  disable_notification=True)
                                  
                # Otherwise, send only the submission link
                else:
                    bot.sendMessage(chat_id=self.chat_ID,
                                    text=message,
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)        
        
        # Reset the last review timestamp
        self.last_reddit_review = end_time
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
                              "til","fun","lrr"]
            
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
            bot.sendMessage(chat_id=self.chat_ID,
                            text=message,
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            # Loop in spoilers of specific set
            cardlist = [spoiler for spoiler in spoilers if spoiler.get("set", None) == set_code]
            scf.send_cards_photos(cardlist, bot, self.chat_ID, disable_notification=True)
        
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