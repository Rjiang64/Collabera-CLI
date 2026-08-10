"""
 Banking App - Encapuslation Demo
"""

 
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.__balance = balance  # private
 
    def deposit(self, amount):
        self.__balance += amount
        return f"New balance: ${self.__balance}"
 
    def withdraw(self, amount):
        if amount > self.__balance:
            return "Not enough funds."
        self.__balance -= amount
        return f"New balance: ${self.__balance}"
 
    def check_balance(self):
        return f"Balance: ${self.__balance}"
 
 
account = BankAccount("Ricky", balance=500)
