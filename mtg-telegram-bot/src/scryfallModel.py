import requests
import json
import logging
import random
from urllib.parse import quote
from time import sleep
from datetime import datetime

"""API Doc : https://scryfall.com/docs/api"""


def get_content(url):
    """Extract data from API json file. If there is multiple pages, gather them."""
    if not url: return False
    # Time limit of scryfall API
    sleep(0.1)
    r = requests.get(url)
    data = {}
    if r.status_code == requests.codes.ok:
        data = json.loads(r.content.decode('utf-8'))
        if data.get("object", False) == "error": 
            logging.info("API respond an error to url : {0}".format(url))
            return False
        if data.get("has_more", None) and data.get("next_page", None):
            content = get_content(data["next_page"])
            data["data"] += content.get("data", [])
    return data


def get_set_list():
    """Get list of all MTG set objects"""
    url = "https://api.scryfall.com/sets"
    content = get_content(url)
    return content.get("data", None)


def get_cards_list(edition):
    """Get list of cards from a set object"""
    url = edition.get("search_uri", False)
    content = get_content(url)
    return content.get("data", None)


def get_futur_sets():
    """Get list of all futur set objects until the last set with a past realease date"""
    present = datetime.now()
    set_list = get_set_list()
    futur_sets = []
    i = 0
    while datetime.strptime(set_list[i].get("released_at", "3000-01-01"),'%Y-%m-%d') > present and i < len(set_list):
        # Doesn't include Magic Online sets
        if not set_list[i].get("digital", False):
            futur_sets.append(set_list[i])
        i += 1
    return futur_sets


def get_image_urls(card, size="normal"):
    """Return a list of normal sized urls for a card object (up to 2 urls for double faced cards)
       Possible sizes: small, normal, large, png, art_crop, border_crop"""
    urls = []
    single_image = card.get("image_uris", {}).get(size, None)
    if single_image:
        urls.append(single_image)
    else:
        for face in card.get("card_faces", []):
            urls.append(face.get("image_uris", {}).get(size, None))
    return urls


def get_card_set(card):
    """Return Set object from a Card object"""
    set_code = card.get("code", None)
    if not set_code: return None
    
    url = "https://api.scryfall.com/sets/{}".format(set_code)
    return get_content(url)


def get_set(set_code):
    """Return set object from a set_code"""
    if not set_code: return None
    url = "https://api.scryfall.com/sets/{}".format(set_code)
    return get_content(url)


def get_card_by_name(name):
    """Return a card object from a string cardname"""
    if not name: return None
    valid_query = quote(name)
    url = "https://api.scryfall.com/cards/named?fuzzy={}".format(valid_query)
    content = get_content(url)
    if not content.get("object", "error") == "error": 
        return content
    else:
        return None


def get_random_card():
    url = "https://api.scryfall.com/cards/random"
    content = get_content(url)
    if not content.get("object", "error") == "error": 
        return content
    else:
        return {}


def get_card_names(card):
    uri = card.get("uri", None)
    if uri:
        url = uri + "/fr"
        content = get_content(url)
    else:
        return None
    if not content.get("object", "error") == "error": 
        card_names = [card.get("name", None), content.get("printed_name", None)]
        return card_names
    else:
        card_names = [card.get("name", None)]
        return card_names


def get_booster_pack(set_code, n=1, p=6, is_pr=False, is_sorted=False):
    """Create n number sealed booster pack with odd of having a foil cards of 1/p
       set is_pr=True to directly have a prerelease pack"""
    # Get all valid set cards without basic lands
    url = "https://api.scryfall.com/cards/search?q=set%3A{}%20is%3Abooster%20-t%3Abasic".format(set_code)
    content = get_content(url)
    if not content.get("object", "error") == "error":
        cards = content.get("data", None)
    else:
        logging.info("No content found at url : {0}".format(url))
        return [], "set not found"

    # Create pool for each rarity
    rarities = {"common": [], "uncommon": [], "rare": [], "mythic": []}
    [rarities.get(card["rarity"], None).append(card) for card in cards]

    pack = []
    notes = ""
    # For prerelease pack we set number of booster to 6 and had a rare or mythic to the pool
    if is_pr:
        n = 6
        if random.choice(range(8)):
            card = random.choice(rarities['rare'])
        else:
            card = random.choice(rarities['mythic'])
        pack.append(card)
        notes += "promo: {}\n".format(card["name"])

    # For regular packs, pick 10 commons, 3 uncommons and 1 rare/mythics + 1/p foil
    for i in range(n):
        # Add 10 commons cards
        random.shuffle(rarities['common'])
        pack += rarities['common'][:10]

        # Add 3 uncommons card
        random.shuffle(rarities['uncommon'])
        pack += rarities['uncommon'][:3]

        # Add rare or mythic card. p of having a mythic is 1/8
        if random.choice(range(8)):
            card = random.choice(rarities['rare'])
        else:
            card = random.choice(rarities['mythic'])
        pack.append(card)

        # Add foil card, odd is 1/p of having one. In general p=6
        if not random.choice(range(p)):
            pack.append(random.choice(cards))
            notes += "foil: {}\n".format(card["name"])

    # Sort by collector number then rarity
    if is_sorted:
        order = {"common": 3, "uncommon": 2, "rare": 1, "mythic": 0}
        pack = sorted(pack, key=lambda k: k['collector_number'])
        pack = sorted(pack, key=lambda d: order[d['rarity']])

    return pack, notes
