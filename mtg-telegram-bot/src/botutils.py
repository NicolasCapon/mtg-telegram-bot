import os
import scryfallModel as scf
from telegram import InputMediaPhoto

def send_cards_photos(cardlist, bot, chat_id, disable_notification=True):
    """Send normalized photos to chat from scryfall card object list"""
    if not cardlist or not isinstance(cardlist, list): return False
    albums = []
    for card in cardlist:
        # Add caption of each card
        cardname = card.get("name", "")
        edition = card.get("set", "unk").upper()
        price = card.get("eur", "?")
        caption = "[{}] {} ({}€)".format(edition, cardname, price)
        for image_url in scf.get_image_urls(card):
            albums.append({"name":cardname, "url":image_url, "caption":caption, "media":InputMediaPhoto(media=image_url, caption=caption)})
            
    # Create n albums of 10 cards max due to the send_media_group function restrictions
    albums = [albums[i:i + 10] for i in range(0, len(albums), 10)]
    for album in albums:
        # Send media or photos from web can cause unpredictable error
        try:
            media = [d['media'] for d in album]
            bot.send_media_group(chat_id=chat_id, media=media, disable_notification=disable_notification, timeout=200)
			# Warning : Sleep can cause some timeout issues
            sleep(3)
        except:
            # If album can be sent try to send photos one by one.
            for card in album:
                try:
                    bot.send_photo(chat_id=chat_id, photo=card["url"])
					# Warning : Sleep can cause some timeout issues
                    sleep(3)
                except:
                    error_msg = "ERROR while sending photo with url={}".format(card["url"])
                    logging.info(error_msg)
                    message = "Je n'arrive pas envoyer la photo de cette carte mais voici le lien : <a href='{}'>{}</a>.".format(card["url"], card["name"])
                    bot.sendMessage(chat_id=chat_id,
                                    text=message,
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)
        
    
    return True
    
def load_members():
    """Load member list from users.json file"""
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "users.json")
    with open(filepath, 'r') as f:
         members = json.load(f)
    
    return members

def register_user(user, ref):
    """Add user to list of users and save list as users.json file"""
    # transform user object to dict for storage
    user_dict = user.__dict__
    # Add GD_deck_dir empty field for google drive
    user_dict["GD_dir_id"] = ""
    ref.append(user_dict)
    
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "users.json")
    with open(filepath, 'w') as f:
        json.dump(ref, f)
    
    return True
    
# def get_member_by_id(member_id):
    # """Return member object from int id"""
    # for member in self.members:
        # if member["id"] == id:
            # return member
    # return None