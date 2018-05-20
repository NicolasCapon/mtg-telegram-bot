import os
import datetime
import json
import botutils as bu

class BudgetModel:
    """Class to manage budget in a group of friend"""
    
    def __init__(self):
        """Load members and unfinished transactions"""
        self.members = bu.load_members()
        self.transactions = self.load_transactions()

    def get_total_debts(self, member_1):
        """Return list of all member debts among other members in group"""
        debt_list = []
        for member in self.members:
            if not member == member_1:
                debt = self.get_debt_between_two_members(member_1, member)
                if debt: debt_list.append(debt)

        return debt_list

    def get_debt_between_two_members(self, member_1, member_2):
        """Calculate the total of all debt between two members. Take member_1 as reference"""
        total = 0
        for transaction in self.transactions:
            if transaction["moneylender"] == member_2 and transaction["recipient"] == member_1:
                total += transaction["amount"]
            elif transaction["moneylender"] == member_1 and transaction["recipient"] == member_2:
                total -= transaction["amount"]
        
        total_debt_dict = {}
        if total > 0:
            total_debt_dict =  {"global_moneylender":member_2, "global_recipient":member_1, "global_amount": round(abs(total), 2)}
        elif total < 0:
            total_debt_dict = {"global_moneylender":member_1, "global_recipient":member_2, "global_amount": round(abs(total), 2)}
        
        return total_debt_dict
        
    def archive_transactions(self, member_1, member_2):
        """All debt has been paid between two members.
           So remove all current transactions between them and archive transactions list in a file
        """
        arch_transactions, left_transactions = [], []
        members = [member_1, member_2]
        for transaction in self.transactions:
            if transaction["moneylender"] in members and transaction["recipient"] in members:
                arch_transactions.append(transaction)
            else:
                left_transactions.append(transaction)
        
        if not arch_transactions: return False
        
        # Archive creation
        archive_date = datetime.datetime.now()
        archive = {"transactions":arch_transactions, "archive_date":archive_date.strftime("%d-%m-%Y %H:%M:%S"), "members":members}
        filename = "archive_{}.json".format(archive_date.strftime("%d%m%Y-%Hh%Mm%Ss"))
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "budget", filename)
        self.dump_transactions(content=archive, filepath=filepath)
        
        # Update transactions list by removing archived transactions
        self.transactions = left_transactions
        self.dump_transactions()
        
        return archive
        
    def add_transaction(self, moneylender, recipient, amount, reason=""):
        """Create a new debt between two members and write it into a file"""
        if amount < 0 : return False
        tr_date = datetime.datetime.now()
        transaction = {"moneylender":moneylender, "recipient":recipient, "amount":round(amount, 2), "reason":reason, "date":tr_date.strftime("%d-%m-%Y %H:%M:%S")}
        
        self.transactions.append(transaction)
        self.dump_transactions()
        
        return transaction
    
    def load_transactions(self):
        """Load all current transactions from file. Return a list of dict"""
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "budget", "transactions.json")
        with open(filepath, 'r') as f:
            transactions = json.load(f)

        return transactions
        
    def update_members(self):
        """Update list of members if new ones are added on the go"""
        members = bu.load_members()
        self.members = members
        return members
        
    def dump_transactions(self, content=None, filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "budget", "transactions.json")):
        """Save current transactions to json file"""
        if content is None: content = self.transactions
        with open(filepath, 'w') as f:
            json.dump(content, f)
        
        return True