import copy
from datetime import datetime

from app.data.sample_data import ACCOUNTS, TRANSACTIONS


class AccountService:

    def __init__(self):
        self.accounts = copy.deepcopy(ACCOUNTS)
        self.transactions = copy.deepcopy(TRANSACTIONS)
        self.next_account_id = max(self.accounts.keys()) + 1
        self.next_transaction_id = max(self.transactions.keys()) + 1

    # ---- accounts ----
    def open_account(self, customer_id, account_type, branch_id, initial_deposit=0):
        account = {
            "id": self.next_account_id,
            "customer_id": customer_id,
            "account_type": account_type,
            "balance": initial_deposit,
            "branch_id": branch_id,
            "created_at": datetime.now(),
            "is_active": True,
        }
        self.accounts[self.next_account_id] = account
        self.next_account_id += 1
        return account

    def get_account(self, account_id):
        return self.accounts.get(account_id)

    def get_all_accounts(self):
        return list(self.accounts.values())

    # ---- transactions ----
    def transfer(self, from_account_id, to_account_id, amount, description=""):
        from_acct = self.accounts.get(from_account_id)
        to_acct = self.accounts.get(to_account_id)

        if from_acct is None or to_acct is None:
            return None  # one of the accounts doesn't exist

        if from_acct["balance"] < amount:
            return None  # not enough money

        # move the money
        from_acct["balance"] -= amount
        to_acct["balance"] += amount

        # log it
        transaction = {
            "id": self.next_transaction_id,
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": amount,
            "type": "TRANSFER",
            "timestamp": datetime.now(),
            "status": "SUCCESS",
            "description": description,
        }
        self.transactions[self.next_transaction_id] = transaction
        self.next_transaction_id += 1
        return transaction

    def get_all_transactions(self):
        return list(self.transactions.values())