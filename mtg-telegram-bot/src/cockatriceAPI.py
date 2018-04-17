import os
import datetime
import scryfallAPI as scf
from lxml import etree

def get_cockatrice_file(set_code):
    """Return a full xml file ready to go for cockatrice custom set folder
       https://github.com/Cockatrice/Cockatrice/wiki/Custom-Cards-&-Sets#to-add-custom-sets-follow-these-steps"""
    xml_tree = etree.Element("cockatrice_carddatabase")
    xml_tree.set("version", "3")
    infos = "Automatically created by mtg-telegram-bot at {}".format(datetime.datetime.now())
    comment = etree.Comment(infos)
    xml_tree.insert(1, comment)
    edition = scf.get_set(set_code.lower())
    # Check if set exists
    if not edition: return False
    add_set_to_xml(xml_tree, edition)
    cards_tree = etree.SubElement(xml_tree, "cards")
    for card in scf.get_cards_list(edition):
        add_card_to_xml(cards_tree, card)
    xml_filename = "{}.xml".format(set_code.upper())
    xml_filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cockatrice", xml_filename)
    print(xml_filepath)
    tree = etree.ElementTree(xml_tree)
    tree.write(open(xml_filepath, 'wb'), xml_declaration=True, encoding='UTF-8')
    return xml_filepath
    
def add_set_to_xml(xml_tree, edition):
    """Get cockatrice xml code from a scryfall set object"""
    # Main element set
    xml_sets = etree.SubElement(xml_tree, "sets")
    xml_set = etree.SubElement(xml_sets, "set")
    # Name and longname
    xml_name = etree.SubElement(xml_set, "name")
    xml_name.text = edition.get("code", "")
    xml_longname = etree.SubElement(xml_set, "longname")
    xml_longname.text = edition.get("name", "")
    # Set type
    xml_type = etree.SubElement(xml_set, "settype")
    xml_type.text = "Custom"
    # Release date
    xml_date = etree.SubElement(xml_set, "releasedate")
    xml_date.text = edition.get("released_at", "")
    
    return True
    
def add_card_to_xml(xml_tree, card):
    """Get cockatrice xml code from a scryfall card object
       https://github.com/Cockatrice/Cockatrice/wiki/Custom-Cards-&-Sets"""
    # Test TODO multicolored card, double faced cards layout == "transform"
    if card.get("layout", "") == "transform":
        # to create relationship between the names
        names = [card_face["name"] for card_face in card["card_faces"]]
        for card_face in card["card_faces"]:
            # Main element card
            xml_card = etree.SubElement(xml_tree, "card")
            # Card name
            xml_name = etree.SubElement(xml_card, "name")
            xml_name.text = card_face["name"]
            # Opposite face card_name
            xml_name = etree.SubElement(xml_card, "related")
            xml_name.text = names.pop()
            # image and set tag
            xml_picURL = etree.SubElement(xml_card, "set")
            xml_picURL.set("picURL", card_face.get("image_uris", {}).get("normal",""))
            xml_picURL.set("rarity", card.get("rarity", ""))
            xml_picURL.text = card["set"].upper()
            # manacost
            manacost = card_face.get("mana_cost").replace("{","").replace("}","")
            if manacost:
                xml_manacost = etree.SubElement(xml_card, "manacost")
                xml_manacost.text = manacost
            # converted mana cost
            cmc = round(card_face.get("cmc", False))
            if cmc : 
                xml_cmc = etree.SubElement(xml_card, "cmc")
                xml_cmc.text = str(cmc)
            # colors
            for color in card_face.get("colors",[]):
                xml_color = etree.SubElement(xml_card, "color")
                xml_color.text = color
            # type
            type = card_face.get("type_line","")
            xml_type = etree.SubElement(xml_card, "type")
            xml_type.text = type
            # Power and toughness
            power = card.get("power", False)
            if power:
                xml_pt = etree.SubElement(xml_card, "pt")
                xml_pt.text = "{}/{}".format(power, card_face["toughness"])
            # tablerow (0 for land, 1 for non-creature, non-land permanents, 2 for creatures, 3 non-permanent cards)
            if "land" in type.lower(): tablerow = "0"
            elif "creature" in type.lower(): tablerow = "2"
            elif "sorcery" in type.lower() or "instant" in type.lower():  tablerow = "3"
            else: tablerow = "1"
            xml_tablerow = etree.SubElement(xml_card, "tablerow")
            xml_tablerow.text = tablerow
            # text
            oracle_text = card_face.get("oracle_text", "")
            xml_text = etree.SubElement(xml_card, "text")
            xml_text.text = oracle_text
            # Come into play tapped
            if "enters the battlefield tapped" in oracle_text:
                xml_cipt = etree.SubElement(xml_card, "cipt")
                xml_cipt.text = "1"
            # loyalty (for planeswalkers only)
            loyalty = card_face.get("loyalty", False)
            if loyalty:
                xml_loyalty = etree.SubElement(xml_card, "loyalty")
                xml_loyalty.text = loyalty
    else:
        # Main element card
        xml_card = etree.SubElement(xml_tree, "card")
        # Name tag
        xml_name = etree.SubElement(xml_card, "name")
        xml_name.text = card["name"]
        # image and set tag 
        # TODO: take double faced card in count
        images = scf.get_image_urls(card)
        xml_picURL = etree.SubElement(xml_card, "set")
        xml_picURL.set("picURL", images[0])
        xml_picURL.set("rarity", card.get("rarity", ""))
        xml_picURL.text = card["set"].upper()
        # manacost
        xml_manacost = etree.SubElement(xml_card, "manacost")
        xml_manacost.text = card.get("mana_cost").replace("{","").replace("}","")
        # converted mana cost
        cmc = round(card.get("cmc",0))
        xml_cmc = etree.SubElement(xml_card, "cmc")
        if not cmc : cmc = ""
        xml_cmc.text = str(cmc)
        # colors
        for color in card.get("colors",[]):
            xml_color = etree.SubElement(xml_card, "color")
            xml_color.text = color
        # type
        type = card.get("type_line","")
        xml_type = etree.SubElement(xml_card, "type")
        xml_type.text = type
        # Power and toughness
        power = card.get("power", False)
        if power:
            xml_pt = etree.SubElement(xml_card, "pt")
            xml_pt.text = "{}/{}".format(power, card["toughness"])
        # tablerow (0 for land, 1 for non-creature, non-land permanents, 2 for creatures, 3 non-permanent cards)
        if "land" in type.lower(): tablerow = "0"
        elif "creature" in type.lower(): tablerow = "2"
        elif "sorcery" in type.lower() or "instant" in type.lower():  tablerow = "3"
        else: tablerow = "1"
        xml_tablerow = etree.SubElement(xml_card, "tablerow")
        xml_tablerow.text = tablerow
        # text
        oracle_text = card.get("oracle_text", "")
        xml_text = etree.SubElement(xml_card, "text")
        xml_text.text = oracle_text
        # Come into play tapped
        if "enters the battlefield tapped" in oracle_text:
            xml_cipt = etree.SubElement(xml_card, "cipt")
            xml_cipt.text = "1"
        # loyalty (for planeswalkers only)
        loyalty = card.get("loyalty", False)
        if loyalty:
            xml_loyalty = etree.SubElement(xml_card, "loyalty")
            xml_loyalty.text = loyalty

    return True