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


# Set up accounts
accounts = {
    "ray": BankAccount("ray", "0000", balance=200),
    "ricky": BankAccount("ricky", "1234", balance=500),
}

# Login
name = input("Enter account name (or q to quit): ").lower()

if name == "q":
    print("Goodbye!")
else:
    account = accounts.get(name)

    if not account:
        print("Account not found.")
    else:
        password = input("Enter PIN (or q to quit): ")

        if password == "q":
            print("Goodbye!")
        elif not account.check_password(password):
            print("Wrong PIN.")
        else:
            while True:
                print("\n1) Deposit 2) Withdraw 3) Balance 4) Quit")
                choice = input("Choose: ").strip()

                if choice == "1":
                    print(account.deposit(float(input("Amount: "))))
                elif choice == "2":
                    print(account.withdraw(float(input("Amount: "))))
                elif choice == "3":
                    print(account.check_balance())
                elif choice == "4":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice.")