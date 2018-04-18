from enum import Enum, auto

class TransactionConvStates(Enum):
    """Enum for transaction Conversation"""
    SELECT_AMOUNT = auto()
    CONFIRM_TRANSACTION = auto()
    VALIDATE = auto()