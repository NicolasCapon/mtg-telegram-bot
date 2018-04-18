from enum import Enum, auto

class TransactionConvStates(Enum):
    """Enum for budgetController transaction Conversation"""
    SELECT_AMOUNT = auto()
    CONFIRM_TRANSACTION = auto()
    VALIDATE = auto()
    
class ArchivingConvStates(Enum):
    """Enum for budgetController archiving Conversation"""
    VERIFY_ARCHIVING = auto()
    CONFIRM_ARCHIVING = auto()