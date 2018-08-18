import os
import json
import random
import logging
import scryfallModel as scf
import redditModel as rm
from operator import itemgetter


class GameModel:
    """Class to manage budget in a group of friend"""
    
    def __init__(self, mode="art"):
        """GameModel constructor"""
        self.user, self.winner, self.id = None, None, None
        if mode == "art":
            logging.info("New art game launched.")
            self.card = self.get_random_card_with_cropped_art()
            self.card_names = scf.get_card_names(self.card)
            logging.info("card_names : {}".format(self.card_names))
            print(self.card_names)
            self.trophy = self.get_trophy()
            self.art_hint = 0
       
    def get_random_card_with_cropped_art(self):
        """Return scryfall card object of a card with cropped art available"""
        card, i  = {}, 0
        while not card.get("image_uris",{}).get("art_crop", False) and i < 20:
            card = scf.get_random_card()
            i += 1
        return card
        
    def is_right_answer(self, answer, user):
        """Check if user answer contains correct card name"""
        answer = answer.lower()
        for card_name in self.card_names:
            if card_name.lower() in answer:
                self.winner = user
                self.write_scores()
                return True
        return False
    
    def get_hint(self):
        """Get hint and hint type on current card quizz"""
        hint_list = ["rarity", "mana_cost", "type_line", "artist", "set_name"]
        if self.art_hint < len(hint_list):
            hint_type = hint_list[self.art_hint]
            hint = self.card[hint_type]
            logging.info("Hint request : " + hint)
            self.art_hint += 1
            return (hint, hint_type.replace("_", " "))
        else:
            return (False, False)
    
    def get_trophy(self):
        """Return trophy image for the winner"""
        reddit = rm.log_to_reddit()
        subreddits = ["babes", "randomsexiness", "sexygirls", "ifyouhadtopickone", "goddesses", "classysexy"]
        subreddit = reddit.subreddit(random.choice(subreddits))
        submissions = list(subreddit.hot(limit=None))
        url = "https://gallery.yopriceville.com/var/resizes/Free-Clipart-Pictures/Trophy-and-Medals-PNG/Transparent_Gold_Cup_Trophy_PNG_Picture.png?m=1507172109"
        has_image, i  = False, 0
        while i < 30 and not has_image:
            i += 1
            submission = random.choice(submissions)
            if hasattr(submission, 'preview') :
                has_image = True
                url = submission.preview.get("images", [])[0].get("source", {}).get("url", url)
                logging.info("Trophy from {} : {}".format(subreddit, submission))

        return url

    def write_scores(self):
        """Update score on json file"""
        logging.info("Game Finished ! Started by {}, won by {}.".format(self.user, self.winner))
        scores = load_scores()
        
        # Verify if user and winner are in score file
        ids = [s["id"] for s in scores]
        if not self.winner.id in ids:
            scores.append({"id": self.winner.id, "won": 0})
        
        # Add score to players
        for score in scores:
            if score["id"] == self.winner.id:
                win_count = score["won"] + 1
                score.update((k, win_count) for k, v in score.items() if k == "won")
                winner_update = True

        logging.info(scores)
        # Write scores
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "games", "art_game_scores.json")
        with open(filepath, 'w') as f:
            json.dump(scores, f)
        
        return scores
     
    def set_user(self, user):
        self.user = user
     
    def set_id(self, id):
        self.id = id


def get_scores():
    """Return list of users sorted on win number"""
    return sorted(load_scores(), key=itemgetter('won'))


def load_scores():
    """Load all current scores from file. Return a list of dict"""
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "games", "art_game_scores.json")
    with open(filepath, 'r') as f:
        scores = json.load(f)

    return scores

