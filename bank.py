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

while True:
    print("\n1) Deposit 2) Withdraw 3) Balance 4) Quit")
    choice = input("Choose: ").strip()

    if choice == "1":
        account.deposit(float(input("Amount: ")))
    elif choice == "2":
        account.withdraw(float(input("Amount: ")))
    elif choice == "3":
        print(account.check_balance())
    elif choice == "4":
        break
    else:
        print("Invalid choice.")
