We developed a simple console-based banking application using Python and Object-Oriented Programming. The main purpose of the application is to allow a user to deposit money, withdraw money, check their balance, and exit the application.

We started by creating a BankAccount class. We used a class because it acts like a blueprint for creating a bank account. Inside the class, we have the account owner's name, balance, and different methods for depositing, withdrawing, and checking the balance.

We used the __init__() method as our constructor. The constructor is automatically called whenever we create an object. In our case, we use a parameterized constructor because we can pass the owner's name and initial balance when creating the account. For example, when we write account = BankAccount("Ricky", balance=500), the constructor automatically stores Ricky as the owner and 500 as the initial balance.

We also use self throughout the class. self refers to the current object. So when we write self.owner, we're referring to the owner of that particular bank account. Similarly, self.__balance refers to the balance belonging to that account.

The main OOP concept we're demonstrating is encapsulation. We made the balance private by using two underscores, like self.__balance. This means we don't want the balance to be directly changed from outside the class. Instead, we control it through methods like deposit(), withdraw(), and check_balance(). This helps protect the data and makes sure the balance is changed in a controlled way.

The deposit() method takes an amount from the user and adds it to the current balance. The withdraw() method subtracts money from the balance, but before doing that, it checks whether the user has enough money. If they try to withdraw more than their balance, it returns a message saying that there are not enough funds. The check_balance() method simply displays the current balance without changing it.

After creating the class, we create an object using account = BankAccount("Ricky", balance=500). This creates an actual bank account object using the BankAccount class. The initial balance for this account is $500.

Then we use a while loop to create the console menu. The user can choose between depositing, withdrawing, checking the balance, or quitting. We use input() to get the user's choice, and we use if, elif, and else statements to determine which operation should run.
