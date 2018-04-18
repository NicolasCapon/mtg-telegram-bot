import datetime
import json

class BudgetModel:
    """Class to manage budget in a group of friend"""
    
    def __init__(self):
        """Load unfinished transactions"""
        self.members = self.load_members()
        self.transactions = self.load_transactions()

    def get_total_debts(self, member_1):
        """Return all member debts among other members in group"""
        debt_list = []
        for member in self.members:
            if not member == member_1:
                debt = self.get_debt_between_two_members(member_1, member)
                if debt: debt_list.append(debt)

        if debt_list: return debt_list
        else: return False

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
            # print("{} doit {}€ à {}".format(member_1, round(abs(total), 2), member_2))
            total_debt_dict =  {"global_moneylender":member_2, "global_recipient":member_1, "global_amount": round(abs(total), 2)}
        elif total < 0:
            # print("{} doit {}€ à {}".format(member_2, round(abs(total), 2), member_1))
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
        
        archive_date = datetime.datetime.now()
        archive = {"transactions":arch_transactions, "archive_date":archive_date.strftime("%d-%m-%Y %H:%M:%S"), "members":members}
        filepath = "/home/pi/telegram/GeekStreamBot/traces/{}-{}_{}.json".format(member_1, member_2, archive_date.strftime("%d%m%Y"))
        # Write down archived transactions
        with open(filepath, 'w') as f:
            json.dump(archive, f)
        
        # Update transactions list by removing archived transactions
        self.transactions = left_transactions
        
        return archive
        
    def add_transaction(self, moneylender, recipient, amount, reason=""):
        """Create a new debt between two members and write it into a file"""
        if amount < 0 : return False
        tr_date = datetime.datetime.now()
        transaction = {"moneylender":moneylender, "recipient":recipient, "amount":round(amount, 2), "reason":reason, "date":tr_date.strftime("%d-%m-%Y %H:%M:%S")}
        self.transactions.append(transaction)
        
        return transaction
        
    def load_members(self):
        """Load member list from file"""
        members = [{"first_name":"Nicolas", "id":1}, {"first_name":"Remi", "id":1}, {"first_name":"Gauthier", "id":1}, {"first_name":"Greg", "id":1}]
        return members
    
    def load_transactions(self):
        """Load all current transactions from file. Return a list of dict"""
        transactions = []
        return transactions
       
    def get_member_by_id(self, member_id):
        """Return member object from int id"""
        for member in self.members:
            if member["id"] == id:
                return member
        return None
        
bm = BudgetManager()
Nicolas = {"first_name":"Nicolas", "id":1}
Remi = {"first_name":"Remi", "id":1}
Gauthier = {"first_name":"Gauthier", "id":1}
bm.add_transaction(Nicolas, "Remi", 3, "1 booster")
bm.add_transaction(Remi, Nicolas, 2.5555, "1 card")
bm.add_transaction(Remi, Nicolas, 1.33333, "1 card")
bm.add_transaction(Remi, Nicolas, 2, "1 card")
bm.add_transaction(Remi, Gauthier, 2, "1 card")
bm.get_debt_between_two_members(Nicolas, Remi)
bm.get_debt_between_two_members(Gauthier, Remi)
bm.add_transaction(Nicolas, Remi, 3, "1 booster")
bm.get_debt_between_two_members(Nicolas, Remi)
print(bm.get_total_debts(Remi))