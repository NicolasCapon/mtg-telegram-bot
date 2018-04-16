from enum import Enum

class Difficulty(Enum):
    
    FACILE = 1
    DIFFICILE = 2
    ABOMINABLE = 3

    def __init__(self, index):
        self.index = index
    
    @property
    def get_card(self):
        if self.index == 1:
            # Genere carte facile
            return 'Rare|Mythic Rare'
        
        if self.index == 2:
            # Genere carte Difficile
            return 'Rare|Mythic Rare'
        
        if self.index == 3:
            # Genere carte Abominable
            return 'Common|Uncommon'
    
    def get_filter(self):
        return '[Facile|Difficile|Abominable]'
    
    def get_table(self):
        return ['Facile', 'Difficile', 'Abominable']
                
class ImageQuizState(Enum):
    START = 1 
    EN_COURS = 2

class SendXML(Enum):
    START = 1 
    MODE = 2

class OpenBoxState(Enum):
    START = 1 
    MANUAL = 2
    BOOST_NUM = 3
    #BOOSTER_PER_BOX = 4
    #MISSING_CARDS = 5

class PriceHandler(Enum):
    FORMAT = 1
    LIST = 2
        
    def get_filter(self):
        return '[Poor|Played|Excellent|Near Mint|Mint]'
    
    def get_table(self):
        return [["Mint"],["Near Mint"],["Excellent"],["Played"],["Poor"]]
    
    def get_condition_list(self,condition):
        conditions = self.get_table()
        ind = conditions.index(condition.lower())
        return conditions[ind:]

class CardScanState(Enum):
    START = 1 