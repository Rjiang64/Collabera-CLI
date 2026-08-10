"""
Banking App - Encapsulation Demo
"""


class BankAccount:
    def __init__(self, owner, password, balance=0):
        self.owner = owner
        self.__password = password  # private
        self.__balance = balance    # private

    def check_password(self, password):
        return password == self.__password

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

    def get_balance(self):
        return self.__balance

    def set_balance(self, balance):
        self.__balance = balance


class SavingsAccount(BankAccount):
 
    def __init__(self, owner, password, balance=0, minimum_balance=100):
        super().__init__(owner, password, balance)
        self.minimum_balance = minimum_balance
        self.account_type = "Savings"
 
    def withdraw(self, amount):
        if amount > self.get_balance():
            return "Not enough funds."
 
        if self.get_balance() - amount < self.minimum_balance:
            return f"Cannot withdraw. Minimum balance of ${self.minimum_balance} must be maintained."
 
        self.set_balance(self.get_balance() - amount)
        return f"Savings - New balance: ${self.get_balance()}"
 
    def deposit(self, amount):
        self.set_balance(self.get_balance() + amount)
        return f"Savings - New balance: ${self.get_balance()}"
 
    def check_balance(self):
        return f"Savings - Balance: ${self.get_balance()}"
 

class CheckingAccount(BankAccount):

    def __init__(self, owner, password, balance=0, overdraft_limit=200):
        super().__init__(owner, password, balance)
        self.overdraft_limit = overdraft_limit
        self.account_type = "Checking"
 
    def withdraw(self, amount):
        if self.get_balance() - amount < -self.overdraft_limit:
            return f"Withdrawal denied. Overdraft limit is ${self.overdraft_limit}."
 
        self.set_balance(self.get_balance() - amount)
        return f"Checking - New balance: ${self.get_balance()}"
 
    def deposit(self, amount):
        self.set_balance(self.get_balance() + amount)
        return f"Checking - New balance: ${self.get_balance()}"
 
    def check_balance(self):
        return f"Checking - Balance: ${self.get_balance()}"
 

class User:
    """User with both checking and savings accounts"""
 
    def __init__(self, name, password, checking_balance=0, savings_balance=0):
        self.name = name
        self.password = password
        self.checking = CheckingAccount(name, password, checking_balance, overdraft_limit=200)
        self.savings = SavingsAccount(name, password, savings_balance, minimum_balance=100)
 
    def verify_password(self, password):
        return password == self.password
 

 
# Set up accounts with both accounts 
users = {
    "ray": User("ray", "0000", checking_balance=500, savings_balance=500),
    "ricky": User("ricky", "1234", checking_balance=500, savings_balance=500),
}
 

# Login
name = input("Enter username (or q to quit): ").lower()
 
if name == "q":
    print("Goodbye!")
else:
    user = users.get(name)
 
    if not user:
        print("Account not found.")
    else:
        password = input("Enter PIN (or q to quit): ")
 
        if password == "q":
            print("Goodbye!")
        elif not user.verify_password(password):
            print("Wrong PIN.")
        else:
            # Main menu - choose account type
            while True:
                print()
                print(f"Welcome {user.name}!")
                print("1) Access Checking Account")
                print("2) Access Savings Account")
                print("3) Quit")
                menu_choice = input("Choose: ").strip()
 
                if menu_choice == "1":
                    # Checking Account Menu
                    account = user.checking
                    while True:
                        print(f"\n--- {account.account_type} Account ---")
                        print("1) Deposit  2) Withdraw  3) Check Balance  4) Back to Main Menu")
                        choice = input("Choose: ").strip()
 
                        if choice == "1":
                            try:
                                amount = float(input("Amount to deposit: $"))
                                if amount <= 0:
                                    print("Amount must be positive.")
                                else:
                                    print(account.deposit(amount))
                            except ValueError:
                                print("Invalid amount.")
 
                        elif choice == "2":
                            try:
                                amount = float(input("Amount to withdraw: $"))
                                if amount <= 0:
                                    print("Amount must be positive.")
                                else:
                                    print(account.withdraw(amount))
                            except ValueError:
                                print("Invalid amount.")
 
                        elif choice == "3":
                            print(account.check_balance())
 
                        elif choice == "4":
                            break
 
                        else:
                            print("Invalid choice.")
 
                elif menu_choice == "2":
                    # Savings Account Menu
                    account = user.savings
                    while True:
                        print(f"\n--- {account.account_type} Account ---")
                        print("1) Deposit  2) Withdraw  3) Check Balance  4) Back to Main Menu")
                        choice = input("Choose: ").strip()
 
                        if choice == "1":
                            try:
                                amount = float(input("Amount to deposit: $"))
                                if amount <= 0:
                                    print("Amount must be positive.")
                                else:
                                    print(account.deposit(amount))
                            except ValueError:
                                print("Invalid amount.")
 
                        elif choice == "2":
                            try:
                                amount = float(input("Amount to withdraw: $"))
                                if amount <= 0:
                                    print("Amount must be positive.")
                                else:
                                    print(account.withdraw(amount))
                            except ValueError:
                                print("Invalid amount.")
 
                        elif choice == "3":
                            print(account.check_balance())
 
                        elif choice == "4":
                            break
 
                        else:
                            print("Invalid choice.")
 
                elif menu_choice == "3":
                    print("Goodbye!")
                    break
 
                else:
                    print("Invalid choice.")