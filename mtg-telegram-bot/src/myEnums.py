from enum import Enum #, auto

class TransactionConvStates(Enum):
    """Enum for budgetController transaction Conversation"""
    SELECT_AMOUNT = 1 # auto()
    CONFIRM_TRANSACTION = 2 # auto()
    VALIDATE = 3 # auto()
    
class ArchivingConvStates(Enum):
    """Enum for budgetController archiving Conversation"""
    VERIFY_ARCHIVING = 1 # auto()
    CONFIRM_ARCHIVING = 2 # auto()